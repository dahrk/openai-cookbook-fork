"""Optional, reconnecting WebSocket telemetry; local JSONL is always retained."""
from __future__ import annotations
from collections import deque
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid
from urllib.parse import urlsplit, urlunsplit


class Cancelled(Exception):
    pass


class Halted(Exception):
    def __init__(self, outcome):
        self.outcome = outcome


class Telemetry:
    def __init__(self, repo, mode, directory='artifacts', delay=0):
        self.run_id = os.getenv('PILOT_RUN_ID') or str(uuid.uuid4())
        self.repo, self.mode, self.delay = repo, mode, delay
        self.phase = 'intake'
        self.seq = 0
        self.pending, self.commands = deque(), deque()
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.paused = False
        self.seen_commands = set()
        self.log = Path(directory) / 'events.jsonl'
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.thread = None
        url = os.getenv('PILOT_SITE_URL')
        if url:
            parsed = urlsplit(url)
            if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost')):
                raise ValueError('PILOT_SITE_URL requires HTTPS (or loopback HTTP)')
            self.url = urlunsplit(('wss' if parsed.scheme == 'https' else 'ws', parsed.netloc, '/socket', '', ''))
            try:
                from websockets.sync.client import connect
            except ImportError:
                raise RuntimeError('Socket telemetry needs: pip install -r requirements-telemetry.txt') from None
            self.connect = connect
            self.thread = threading.Thread(target=self._network, daemon=True)
            self.thread.start()

    def emit(self, phase=None, detail='', status='running', metrics=None):
        with self.lock:
            if phase:
                self.phase = phase
            self.seq += 1
            event = {'run_id': self.run_id, 'seq': self.seq, 'repo': self.repo, 'mode': self.mode,
                'phase': self.phase, 'status': status, 'detail': detail[:2000], 'metrics': metrics or {}}
            with self.log.open('a') as out:
                out.write(json.dumps(event) + '\n')
            self.pending.append({'type': 'event', 'event': event})
        return event

    def boundary(self, phase, detail='', metrics=None):
        self.checkpoint()
        self.emit(phase, detail, metrics=metrics)
        if self.delay:
            end = time.monotonic() + self.delay
            while time.monotonic() < end:
                self.checkpoint()
                time.sleep(.1)

    def checkpoint(self):
        while True:
            with self.lock:
                commands = list(self.commands)
                self.commands.clear()
            for command in commands:
                command_id = command['id']
                if command_id in self.seen_commands:
                    continue
                self.seen_commands.add(command_id)
                action = command['action']
                if action == 'pause':
                    self.paused = True
                elif action == 'resume':
                    self.paused = False
                elif action == 'cancel':
                    self.emit(detail='Cancelled at a cooperative boundary', status='cancelled')
                    self._ack(command_id)
                    raise Cancelled()
                elif action in ('needs_human_review', 'wont_implement'):
                    self._ack(command_id)
                    raise Halted(action)
                self.emit(detail=action + ' applied at a cooperative boundary', status='paused' if self.paused else 'running')
                self._ack(command_id)
            if not self.paused:
                return
            time.sleep(.1)

    def _ack(self, command_id):
        with self.lock:
            self.pending.append({'type': 'ack', 'run_id': self.run_id, 'command_id': command_id})

    def require_delivery(self, timeout=30):
        """Fail a connected integration run rather than silently keeping events local."""
        if not self.thread:
            raise RuntimeError('Required Site telemetry is not configured')
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                if not self.pending:
                    return
            time.sleep(.05)
        raise RuntimeError('Site did not acknowledge telemetry before the delivery deadline')

    def _network(self):
        delay = 1
        while not self.stop.is_set():
            try:
                headers = {}
                token = os.getenv('PILOT_SITE_BEARER')
                if token:
                    headers['OAI-Sites-Authorization'] = 'Bearer ' + token
                with self.connect(self.url, additional_headers=headers, open_timeout=10, close_timeout=2, max_size=1_000_000) as ws:
                    delay = 1
                    while not self.stop.is_set():
                        with self.lock:
                            message = self.pending[0] if self.pending else {'type': 'heartbeat', 'run_id': self.run_id}
                        ws.send(json.dumps(message))
                        reply = json.loads(ws.recv(timeout=15))
                        if reply.get('type') == 'error':
                            raise RuntimeError('Relay rejected telemetry')
                        with self.lock:
                            if self.pending and self.pending[0] is message:
                                self.pending.popleft()
                            self.commands.extend(reply.get('commands', []))
                        if message['type'] == 'heartbeat':
                            self.stop.wait(1)
            except Exception as error:
                # Avoid leaking headers or URLs in exception strings.
                print(f'Issue Pilot relay disconnected ({type(error).__name__}); local events retained; retry in {delay}s', file=sys.stderr)
                self.stop.wait(delay)
                delay = min(delay * 2, 30)

    def close(self):
        # Give buffered events a bounded opportunity to flush without hanging CI.
        deadline = time.monotonic() + (3 if self.thread else 0)
        while self.pending and self.thread and time.monotonic() < deadline:
            time.sleep(.05)
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=1)
