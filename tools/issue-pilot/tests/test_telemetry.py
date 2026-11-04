import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from telemetry import Telemetry, Cancelled


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        environment = patch.dict(os.environ, {'PILOT_SITE_URL': '', 'PILOT_RUN_ID': ''})
        environment.start()
        self.addCleanup(environment.stop)
        self.t = Telemetry('demo/cookbook', 'demo', self.temp.name)

    def test_offline_events_are_ordered_and_retained(self):
        self.t.boundary('intake', 'Read issues')
        self.t.boundary('group', 'Classify reports', {'issues': 7})
        self.t.emit(status='completed')
        events = [json.loads(line) for line in self.t.log.read_text().splitlines()]
        self.assertEqual([e['seq'] for e in events], [1, 2, 3])
        self.assertEqual(events[-1]['status'], 'completed')
        self.assertEqual(len({e['run_id'] for e in events}), 1)

    def test_pause_waits_for_resume_and_acknowledges_once(self):
        self.t.commands.append({'id': 'pause-1', 'action': 'pause'})
        timer = threading.Timer(.15, lambda: self.t.commands.append({'id': 'resume-1', 'action': 'resume'}))
        timer.start()
        self.t.checkpoint()
        timer.join()
        self.assertFalse(self.t.paused)
        acks = [m['command_id'] for m in self.t.pending if m['type'] == 'ack']
        self.assertEqual(acks, ['pause-1', 'resume-1'])
        self.t.commands.append({'id': 'pause-1', 'action': 'pause'})
        self.t.checkpoint()
        self.assertFalse(self.t.paused)

    def test_cancel_is_acknowledged_after_terminal_event(self):
        self.t.commands.append({'id': 'cancel-1', 'action': 'cancel'})
        with self.assertRaises(Cancelled):
            self.t.checkpoint()
        messages = list(self.t.pending)
        self.assertEqual(messages[-2]['event']['status'], 'cancelled')
        self.assertEqual(messages[-1], {'type': 'ack', 'run_id': self.t.run_id, 'command_id': 'cancel-1'})

    def test_non_tls_remote_is_rejected(self):
        with patch.dict(os.environ, {'PILOT_SITE_URL': 'http://example.com'}):
            with self.assertRaises(ValueError):
                Telemetry('demo/cookbook', 'demo', self.temp.name)

    def test_required_delivery_rejects_an_offline_only_run(self):
        self.t.emit(detail='A real integration requires a remote receipt')
        with self.assertRaisesRegex(RuntimeError, 'not configured'):
            self.t.require_delivery(timeout=0)
