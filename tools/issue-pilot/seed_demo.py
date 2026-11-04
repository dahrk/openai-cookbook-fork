"""Seed synthetic reports on your fork; requires GH_TOKEN, never writes upstream."""
import argparse
import json
from pilot import GitHub, ROOT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', required=True)
args = parser.parse_args()
if args.repo.lower() == 'openai/openai-cookbook':
    parser.error('Use a demo fork')
api = GitHub(args.repo)
existing = api.pages('/issues?state=all')
for issue in json.loads((ROOT / 'fixtures/issues.json').read_text()):
    marker = f'<!-- issue-pilot-fixture:{issue["number"]} -->'
    if any(marker in (i.get('body') or '') for i in existing):
        print(f'Skipped existing fixture {issue["number"]}')
        continue
    created = api.call('/issues', {'title': '[SYNTHETIC DEMO] ' + issue['title'],
        'body': 'Synthetic report for an Issue Pilot demonstration. This is not a verified '
                'upstream defect.\n\nObserved scenario: ' + issue['title'] +
                '\n\nExpected demo diagnosis: ' + issue['root_cause'] +
                '\n\nFor this scenario only, propose a short README clarification.\n\n' + marker})
    print('Created #' + str(created['number']))
