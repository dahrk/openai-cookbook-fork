"""Record model decision latency without prompts, outputs or credentials."""
import json
from pathlib import Path
import time

from codex_brain import selected_model


class MeasuredBrain:
    def __init__(self, brain, backend, output):
        self.brain, self.backend = brain, backend
        self.path = Path(output) / 'request-metrics.jsonl'

    def _call(self, operation, *args):
        started, status = time.perf_counter(), 'completed'
        self.brain.last_request = None
        try:
            return getattr(self.brain, operation)(*args)
        except Exception as error:
            status = type(error).__name__
            raise
        finally:
            row = {'backend': self.backend, 'model': selected_model(),
                   'operation': operation, 'seconds': time.perf_counter() - started,
                   'status': status}
            if isinstance(self.brain.last_request, dict):
                row['provider'] = self.brain.last_request
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a') as output:
                output.write(json.dumps(row) + '\n')

    def classify(self, *args):
        return self._call('classify', *args)

    def fix(self, *args):
        return self._call('fix', *args)

    def review(self, *args):
        return self._call('review', *args)
