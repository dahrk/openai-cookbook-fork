# Eight-minute presenter script

Before starting, run `python pilot.py demo`, open `artifacts/index.html`, and keep the terminal, `artifacts/proposed-fix.diff`, workflow YAML, and `pilot.py` ready. No installation or credentials are required for the replay. This script is an eight-minute presentation, not an eight-minute runtime.

| Time | Show | Narration / action |
|---|---|---|
| 0:00–0:45 | Report title and flow | “This worker turns repeated GitHub issue reports into a ranked fix queue. Report count is our explicit proxy for impact. Today we're using Cookbook-shaped synthetic reports.” |
| 0:45–1:30 | `.github/workflows/issue-pilot.yml` | “GitHub Actions runs hourly. The Agents SDK makes semantic decisions; ordinary Python owns persistence and side effects. Manual dispatch runs the same worker. This replay is offline and uses a compressed clock.” |
| 1:30–2:30 | Terminal: `python pilot.py demo`; fixture JSON | “Seven distinct reports collapse to three root causes: four data-path reports, two API-key setup reports, one broken link. The four-report group wins. In live mode an SDK agent compares specific root causes and uncertain matches stay separate.” |
| 2:30–3:30 | `artifacts/proposed-fix.diff`; report | “The demo proposes one README clarification and opens mock draft PR #201. The live worker uses a real model, writes only allowlisted Markdown, checks boundaries, and opens a real draft PR. A human and repository CI decide whether it is right.” |
| 3:30–4:30 | Run-history entry: second run | “The next scheduled intake remembers the issue IDs and checks GitHub for the group's stable branch. It finds the existing PR. Four reports stay four; no duplicate fix. State is stored on a dedicated branch rather than a short-lived CI cache.” |
| 4:30–5:30 | Run-history entry: +49h | “We mark the mock PR ready. Then we advance the simulated clock 49 hours. No human review of the current commit exists, so the configured path owner is tagged. This comment is simulated; live owner handles come from configuration.” |
| 5:30–6:15 | Run-history retry entry | “Retrying the run finds the comment marker and sends nothing. A new head commit gets a fresh review check; a review on an older commit doesn't hide an unreviewed change.” |
| 6:15–7:00 | Merged PR card and final history entry | “The fix merges. A fifth duplicate joins the same root cause later, but its closed or merged PR is still remembered. The automation won't open the same fix again. A regression or rejected fix requires a human decision.” |
| 7:00–7:40 | Tests: `python -m unittest discover -s tests -v` | “These checks exercise repeated intake, PR recovery, stale review rules, duplicate reminder prevention, owner routing, and file boundaries. The patch was also checked against a shallow real Cookbook checkout.” |
| 7:40–8:00 | README activation steps | “The remaining integration gates are OpenAI and GitHub credentials, your fork and owner handles, and uploading the workflow. The scheduled worker and real SDK adapters are implemented. We have not claimed this mock PR exists on GitHub.” |

If asked why not fix notebooks automatically: the demo deliberately bounds the autonomous action to reviewable documentation. The agent declines unsupported fixes. A sandboxed coding worker can later replace that adapter without changing intake, ranking, memory or reminders.

If asked why no repeated reminders: one reminder per head SHA is the chosen policy, so a retry doesn't create notification spam. Escalation cadence can be added as a separate policy.

If asked whether all fixes are validated: only file policy and whitespace are checked automatically here. The PR remains a draft and requires review and repository CI. The synthetic example is illustrative, not a verified upstream bug.
