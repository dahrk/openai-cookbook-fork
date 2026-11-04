from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmark import run_case, HEAD


class Brain:
    def classify(self, issue, groups):
        return 'NEW', 'Empty heading', 1

    def fix(self, group, path, content):
        return {'actionable': True, 'explanation': 'Remove empty heading',
                'path': path, 'content': HEAD}

    def review(self, evidence):
        return {'summary': 'Only the empty heading was removed.', 'findings': [],
                'limitations': 'Static supplied text only.'}


class BenchmarkTests(unittest.TestCase):
    def test_all_routes_use_real_orchestration_with_only_fixture_github_effects(self):
        for backend in ['codex', 'agents_api']:
            for route, effect in [('implement', 'draft_pr'), ('review', 'review'),
                                  ('needs_human_review', None), ('wont_implement', 'issue')]:
                with self.subTest(backend=backend, route=route), tempfile.TemporaryDirectory() as folder, \
                        patch('pilot.make_brain', return_value=Brain()) as brain:
                    result = run_case(backend, route, Path(folder))
                    self.assertEqual(result['status'], 'wont_implement' if route == 'wont_implement'
                                     else 'needs_human_review')
                    self.assertEqual([item['kind'] for item in result['fixture_effects']],
                                     [effect] if effect else [])
                    if route in ('needs_human_review', 'wont_implement'):
                        brain.assert_not_called()
                    if route == 'review':
                        self.assertEqual(result['fixture_effects'][0]['event'], 'COMMENT')
                    self.assertEqual(result['path'][-1]['status'], result['status'])


if __name__ == '__main__':
    unittest.main()
