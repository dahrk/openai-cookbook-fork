"""Compare live Luna inference through both runtimes using isolated effect fixtures.

This exercises pilot.live end to end, but GitHub effects are deliberately local
fixtures. It never sends a Site event, opens a PR, or closes a real issue. Real
GitHub/Actions integration runs are reported separately from these measurements.
"""
import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

import pilot
from telemetry import Telemetry

BASE = '# Cookbook\n\n<h3></h3>\n\n[Guide](https://example.com/guide)\n\n## License\n\nMIT\n'
HEAD = BASE.replace('<h3></h3>\n\n', '')
PATCH = '@@ -1,7 +1,5 @@\n # Cookbook\n \n-<h3></h3>\n-\n [Guide](https://example.com/guide)\n \n ## License'
ISSUE = {'number': 1, 'title': 'Remove the empty README heading',
         'body': 'Remove only the empty <h3></h3> heading and adjacent blank line. '
                 'Keep all links and substantive text.\n\n### Pull request number\n\n5\n\n'
                 '### Review focus\n\nCheck only empty heading removal, links and substantive text.',
         'user': {'login': 'dahrk'}, 'state': 'open', 'html_url': 'https://benchmark.test/issues/1'}


class FixtureGitHub:
    def __init__(self, repo):
        self.repo, self.effects = repo, []

    def call(self, path, data=None, method=None):
        if path == '/issues/1':
            if data:
                self.effects.append({'kind': 'issue', **data})
            return dict(ISSUE)
        if path == '/pulls/5':
            return {'number': 5, 'state': 'open', 'changed_files': 1,
                    'base': {'sha': 'base', 'repo': {'full_name': self.repo}},
                    'head': {'sha': 'head', 'repo': {'full_name': self.repo}}}
        if path.startswith('/contents/README.md?ref='):
            content = BASE if path.endswith('base') else HEAD
            return {'type': 'file', 'encoding': 'base64', 'size': len(content),
                    'content': base64.b64encode(content.encode()).decode()}
        if path == '/pulls/5/reviews' and data:
            self.effects.append({'kind': 'review', 'event': data['event'], 'commit_id': data['commit_id']})
            return {'html_url': 'https://benchmark.test/reviews/1'}
        raise AssertionError('Unexpected fixture endpoint: ' + path)

    def pages(self, path):
        if path == '/pulls/5/files':
            return [{'filename': 'README.md', 'patch': PATCH}]
        if path == '/pulls/5/reviews':
            return []
        raise AssertionError('Unexpected fixture list: ' + path)

    def find_pr(self, key):
        return None


def fixture_fix(api, brain, key, group, config):
    proposal = brain.fix(group, 'README.md', BASE)
    with tempfile.TemporaryDirectory() as folder:
        Path(folder, 'README.md').write_text(BASE)
        destination = pilot.bounded_proposal(proposal, config, folder)
        if not destination:
            return None, proposal['explanation']
    api.effects.append({'kind': 'draft_pr', 'path': 'README.md'})
    return {'number': 901, 'state': 'open', 'draft': True,
            'head': {'sha': 'fixture-head'}}, 'Fixture draft README PR'


def run_case(backend, route, output):
    output.mkdir(parents=True, exist_ok=True)
    api = FixtureGitHub(pilot.TARGET_REPO)
    environment = {'PILOT_BACKEND': backend, 'OPENAI_MODEL': 'gpt-6-luna',
                   'PILOT_SITE_URL': '', 'PILOT_SITE_BEARER': '',
                   'PILOT_REQUIRE_TELEMETRY': '0', 'PILOT_RUN_ID': 'benchmark-' + backend + '-' + route}
    with patch.dict(os.environ, environment), patch('pilot.GitHub', return_value=api), \
            patch('pilot.open_fix', side_effect=fixture_fix), redirect_stdout(io.StringIO()):
        telemetry = Telemetry(pilot.TARGET_REPO, 'live', output)
        args = SimpleNamespace(repo=pilot.TARGET_REPO, issue_number=1, disposition=route,
            source_repo=None, issue_limit=0, state=str(output / 'state.json'),
            output=str(output), max_fixes=1, telemetry=telemetry)
        started = time.perf_counter()
        try:
            pilot.live(args)
            status = args.outcome
        except Exception as error:
            status = 'failed'
            telemetry.emit(status='failed', detail='Benchmark stopped: ' + type(error).__name__)
        finally:
            elapsed = time.perf_counter() - started
            telemetry.close()
    events = [json.loads(line) for line in (output / 'events.jsonl').read_text().splitlines()]
    metrics = output / 'request-metrics.jsonl'
    requests = [json.loads(line) for line in metrics.read_text().splitlines()] if metrics.exists() else []
    return {'backend': backend, 'route': route, 'status': status, 'seconds': elapsed,
            'path': [{'phase': event['phase'], 'status': event['status']} for event in events],
            'model_requests': requests, 'fixture_effects': api.effects}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=['codex', 'agents_api', 'both'], default='both')
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--output', default='benchmark-results')
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 3:
        parser.error('Use 1–3 repetitions to bound demo costs')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    backends = ['codex', 'agents_api'] if args.backend == 'both' else [args.backend]
    # Serial, alternating order across repetitions; never consumes parallel runners.
    for repetition in range(args.repetitions):
        for backend in backends[::1 if repetition % 2 == 0 else -1]:
            for route in ['implement', 'review', 'needs_human_review', 'wont_implement']:
                result = run_case(backend, route, output / str(repetition + 1) / backend / route)
                result['repetition'] = repetition + 1
                results.append(result)
                (output / 'results.json').write_text(json.dumps({'scope': 'live inference, fixture GitHub effects; no Site writes',
                    'model': 'gpt-6-luna', 'reasoning': 'low', 'host': platform.platform(),
                    'fixture_sha256': hashlib.sha256((BASE + HEAD + PATCH + json.dumps(ISSUE, sort_keys=True)).encode()).hexdigest(),
                    'results': results}, indent=2))
                print(f'{backend:10} {route:19} {result["status"]:19} {result["seconds"]:.3f}s', flush=True)
    print('Results:', output / 'results.json')
    if any(result['status'] != ('wont_implement' if result['route'] == 'wont_implement'
                               else 'needs_human_review') for result in results):
        raise SystemExit('One or more paths failed; inspect results.json')


if __name__ == '__main__':
    main()
