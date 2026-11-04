import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import pilot

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.issues = json.loads((pilot.ROOT / 'fixtures/issues.json').read_text())

    def test_repeated_intake_preserves_group_and_pr(self):
        groups = {}
        rank = pilot.ingest(self.issues, groups, pilot.MockBrain())
        self.assertEqual([len(groups[k]['reports']) for k in rank], [4, 2, 1])
        groups[rank[0]]['pr'] = {'number': 42, 'state': 'closed', 'merged': True}
        pilot.ingest(self.issues + [dict(self.issues[0], number=999)], groups, pilot.MockBrain())
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[rank[0]]['reports']), 5)
        self.assertTrue(groups[rank[0]]['pr']['merged'])

    def test_remote_pr_recovery_and_fix_budget(self):
        groups = {}
        rank = pilot.ingest(self.issues, groups, pilot.MockBrain())
        top = rank[0]
        class Remote:
            def find_pr(self, key):
                return {'number': 77, 'state': 'closed', 'merged': True} if key == top else None
            def refresh(self, pr):
                return pr
        attempts, checkpoints = [], []
        def create(api, brain, key, group, config):
            attempts.append(key)
            return {'number': 78, 'state': 'open'}, 'Created'
        pilot.reconcile_fixes(Remote(), None, rank, groups, {'min_reports': 2}, 1,
                              lambda: checkpoints.append(True), create)
        self.assertEqual(groups[top]['pr']['number'], 77)
        self.assertEqual(attempts, [rank[1]])
        self.assertEqual(len(checkpoints), 3)

    def test_missing_recorded_pr_fails_closed(self):
        class Missing:
            def find_pr(self, key):
                return None
        groups = {'g': {'reports': {'1': 'a', '2': 'b'}, 'pr': {'number': 42}}}
        def forbidden(*args):
            self.fail('Must not create another fix')
        with self.assertRaises(RuntimeError):
            pilot.reconcile_fixes(Missing(), None, ['g'], groups, {'min_reports': 2}, 1,
                                  create_fix=forbidden)

    def test_low_confidence_does_not_merge(self):
        class Uncertain:
            def classify(self, issue, groups):
                return 'existing', 'Different defect', .5
        groups = {'existing': {'summary': 'One defect', 'reports': {}, 'pr': None}}
        pilot.ingest([{'number': 1, 'title': 'Something'}], groups, Uncertain())
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups['existing']['reports'], {})

    def test_review_sla_current_commit_human_only(self):
        t = datetime(2026, 1, 1, tzinfo=timezone.utc)
        pr = {'state': 'open', 'draft': False, 'head': {'sha': 'current'}}
        due = lambda reviews: pilot.review_due(pr, reviews, pilot.stamp(t), t + timedelta(hours=49), 48)
        self.assertTrue(due([]))
        self.assertFalse(pilot.review_due(pr, [], pilot.stamp(t), t + timedelta(hours=47), 48))
        self.assertTrue(due([{'commit_id': 'old', 'state': 'APPROVED'}]))
        self.assertTrue(due([{'commit_id': 'current', 'state': 'PENDING'}]))
        self.assertTrue(due([{'commit_id': 'current', 'state': 'APPROVED', 'user': {'type': 'Bot'}}]))
        self.assertFalse(due([{'commit_id': 'current', 'state': 'COMMENTED', 'user': {'type': 'User'}}]))
        pr['draft'] = True
        self.assertFalse(due([]))
        pr.update(draft=False, state='closed')
        self.assertFalse(due([]))

    def test_comment_marker_prevents_repeat(self):
        api = object.__new__(pilot.GitHub)
        comments, calls = [], []
        api.pages = lambda path: comments
        def call(path, data):
            calls.append(data)
            comments.append(data)
        api.call = call
        self.assertTrue(api.comment_once(42, '<!-- key -->', '@owner review'))
        self.assertFalse(api.comment_once(42, '<!-- key -->', '@owner review'))
        self.assertEqual(len(calls), 1)

    def test_proposal_bounds_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            p = Path(d) / 'README.md'
            p.write_text('old')
            config = {'fix_paths': ['README.md', '../escape.md']}
            proposal = {'actionable': True, 'path': 'README.md', 'content': 'new'}
            self.assertEqual(pilot.bounded_proposal(proposal, config, d), p.resolve())
            for path in ['../escape.md', '.github/workflows/attack.yml']:
                with self.assertRaises(ValueError):
                    pilot.bounded_proposal(dict(proposal, path=path), config, d)
            p.unlink()
            target = Path(outside) / 'README.md'
            target.write_text('outside')
            p.symlink_to(target)
            with self.assertRaises(ValueError):
                pilot.bounded_proposal(proposal, config, d)

    def test_owner_routing(self):
        config = {'owners': {'examples/*': ['@alice'], 'docs/*': ['@team/docs']},
                  'fallback_owners': ['@maintainer']}
        self.assertEqual(pilot.owner_mentions(config, ['examples/demo.ipynb']), '@alice')
        self.assertEqual(pilot.owner_mentions(config, ['other']), '@maintainer')

    def test_live_batch_reads_upstream_and_keeps_target_and_source_in_state(self):
        reads = []
        fixtures = self.issues
        class API:
            def __init__(self, repo):
                self.repo = repo
            def issues(self):
                reads.append(self.repo)
                return [dict(issue, user={'login': 'dahrk'}) for issue in fixtures]
            def find_pr(self, key):
                self_repo = self.repo
                self_outer.assertEqual(self_repo, 'dahrk/openai-cookbook-fork')
                return None
        self_outer = self
        telemetry = SimpleNamespace(boundary=lambda *a: None, checkpoint=lambda: None)
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(repo='dahrk/openai-cookbook-fork',
                source_repo='openai/openai-cookbook', issue_limit=2, max_fixes=0,
                state=directory + '/state.json', output=directory + '/artifacts', telemetry=telemetry)
            with patch('pilot.GitHub', API), patch('pilot.CodexBrain', pilot.MockBrain), \
                 patch.dict('os.environ', {'OPENAI_MODEL': 'gpt-6-luna',
                     'PILOT_BACKEND': 'codex', 'PILOT_REQUIRE_TELEMETRY': '0'}):
                pilot.live(args)
            state = json.loads(Path(args.state).read_text())
        self.assertEqual(reads, ['openai/openai-cookbook'])
        self.assertEqual(state['repo'], 'dahrk/openai-cookbook-fork')
        self.assertEqual(state['source_repo'], 'openai/openai-cookbook')
        self.assertEqual(sum(len(group['reports']) for group in state['groups'].values()), 2)

    def test_issue_author_gate_and_form_defaults(self):
        api = SimpleNamespace(repo=pilot.TARGET_REPO, call=lambda path: {
            'number': 1, 'state': 'open', 'user': {'login': 'someone-else'}})
        with self.assertRaisesRegex(ValueError, 'authored by @dahrk'):
            pilot.authorized_issue(api, 1)
        self.assertEqual(pilot.issue_outcome({'body': 'Ordinary report'}), 'needs_human_review')
        for label, outcome in pilot.OUTCOMES.items():
            self.assertEqual(pilot.issue_outcome({'body': '### Pilot outcome\n\n'+label+'\n\n### Report\ntext'}), outcome)
        with self.assertRaises(ValueError):
            pilot.issue_outcome({'body': '### Pilot outcome\n\nrun arbitrary code'})

    def test_human_review_keeps_issue_open_and_wont_implement_closes_not_planned(self):
        calls = []
        class API:
            def __init__(self, repo):
                self.repo = repo
            def call(self, path, data=None, method=None):
                calls.append((path, data, method))
                return {'number': 1, 'state': 'open', 'user': {'login': 'dahrk'},
                        'html_url': 'https://github.com/dahrk/openai-cookbook-fork/issues/1'}
        events = []
        with tempfile.TemporaryDirectory() as directory, patch('pilot.GitHub', API):
            args = SimpleNamespace(repo=pilot.TARGET_REPO, issue_number=1, output=directory,
                telemetry=SimpleNamespace(run_id='test', emit=lambda **event: events.append(event)))
            pilot.terminal_outcome(args, 'needs_human_review')
            self.assertFalse(any(data for _, data, _ in calls))
            pilot.terminal_outcome(args, 'wont_implement')
        self.assertEqual(calls[-1], ('/issues/1', {'state': 'closed', 'state_reason': 'not_planned'}, 'PATCH'))
        self.assertEqual([event['status'] for event in events], ['needs_human_review','wont_implement'])

if __name__ == '__main__':
    unittest.main()
