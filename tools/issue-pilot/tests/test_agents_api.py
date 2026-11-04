import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agents_api_brain import AgentsAPIBrain
from request_metrics import MeasuredBrain
from pilot import issue_backend


def stream(events):
    return io.BytesIO(''.join('data: ' + json.dumps(event) + '\n\n' for event in events).encode())


class AgentsAPITests(unittest.TestCase):
    def test_luna_request_disables_sandbox_tools_and_delegation_and_deletes_session(self):
        events = [{'type': 'agent.session.created', 'session': {'id': 'sess_test'}},
            {'type': 'agent.session.turn.output_text.delta', 'item_id': 'answer', 'delta': 'partial'},
            {'type': 'agent.session.turn.output_text.done', 'item_id': 'answer',
             'text': '{"group_id":"NEW","summary":"Empty heading","confidence":1}'},
            {'type': 'agent.session.turn.completed', 'turn': {'subagent_id': None}}]
        requests = []
        def invoke(request, **kwargs):
            requests.append(request)
            if request.get_method() == 'DELETE':
                return io.BytesIO(b'{}')
            payload = json.loads(request.data)
            self.assertEqual(payload['agent']['model'], 'gpt-6-luna')
            self.assertEqual(payload['agent']['reasoning'], {'effort': 'low'})
            self.assertEqual(payload['environment'], {'type': 'none'})
            self.assertEqual(payload['agent']['tools'], [])
            self.assertFalse(payload['agent']['multi_agent']['enabled'])
            self.assertNotIn('test-secret', request.data.decode())
            return stream(events)
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret'}), patch('agents_api_brain.urlopen', side_effect=invoke):
            brain = AgentsAPIBrain()
            self.assertEqual(brain.classify({'number': 1, 'title': 'Heading'}, {})[0], 'NEW')
        self.assertEqual(requests[-1].get_method(), 'DELETE')
        self.assertEqual(brain.last_request['status'], 'completed')

    def test_idle_or_subagent_completion_never_establishes_root_success(self):
        for event in [{'type': 'agent.session.idle'},
                      {'type': 'agent.session.turn.completed', 'turn': {'subagent_id': 'other'}}]:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'key'}), \
                    patch('agents_api_brain.urlopen', return_value=stream([event])):
                with self.assertRaisesRegex(RuntimeError, 'before the root turn completed'):
                    AgentsAPIBrain().classify({'number': 1}, {})

    def test_metrics_contain_no_evidence_outputs_or_credentials(self):
        class Brain:
            def classify(self, *args):
                return 'NEW', 'private result', 1
        with tempfile.TemporaryDirectory() as directory:
            measured = MeasuredBrain(Brain(), 'agents_api', directory)
            measured.classify({'private': 'secret evidence'}, {})
            row = Path(directory, 'request-metrics.jsonl').read_text()
            self.assertNotIn('private', row)
            self.assertNotIn('secret', row)
            self.assertEqual(json.loads(row)['operation'], 'classify')

    def test_issue_runtime_is_allowlisted_and_defaults_to_cli(self):
        self.assertEqual(issue_backend({}), 'codex')
        self.assertEqual(issue_backend({'body': '### Execution backend\n\nAgents API (managed Codex)'}), 'agents_api')
        with self.assertRaises(ValueError):
            issue_backend({'body': '### Execution backend\n\nother'})


if __name__ == '__main__':
    unittest.main()
