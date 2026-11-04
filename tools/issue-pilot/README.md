# Issue Pilot

An eight-minute demo of scheduled GitHub issue intake → semantic duplicate grouping → impact ranking → draft fixes → stale-review owner reminders. Uses **GitHub Actions + the OpenAI Agents SDK**, with a credential-free replay. Everything runs locally except authenticated GitHub/OpenAI calls.

## Run the demo now

Requires Python 3.11+. The replay uses only the standard library:

```sh
cd /workspace/issue-pilot
python pilot.py demo
python -m unittest discover -s tests -v
```

Open `artifacts/index.html` for the report and `artifacts/proposed-fix.diff` for the sample fix. The replay compresses 72 hours into seconds; its timestamps, issues, PR #201, model decisions, and owner mentions are **simulated**. No external comments or PRs are created. Run it again to reset the scenario.

Follow [the eight-minute presenter script](docs/DEMO.md). A shallow, sparse checkout of the real Cookbook is available locally under `vendor/openai-cookbook`; the fixture README and MIT license are bundled so the replay remains offline and portable.

## What runs live

`.github/workflows/issue-pilot.yml` runs hourly (UTC) and supports manual dispatch. Scheduled mode defaults to `demo` until repository variable `PILOT_MODE=live` is set. GitHub schedules are best effort, may be delayed, and require this workflow on the default branch. Inactive public repositories may have schedules disabled by GitHub. The installed workflow defaults to demo mode. Validate it with a manual demo dispatch before configuring live credentials.

1. Read every open issue, excluding PRs; paginate rather than silently dropping reports.
2. Agents SDK structured output compares each new issue with persisted root causes. Confidence below 0.85 makes a separate group. Previously seen issue IDs retain their group.
3. Rank by the cumulative number of distinct issue reports, descending. This demo deliberately treats report count as impact; reactions and severity are not additional weights. Historical reports stay counted after closure. A repeated issue contributes once.
4. Reconcile existing open, closed, and merged PRs using stable per-group branch names. Reuse any prior PR. Closed unmerged PRs require manual intervention rather than automatic reopening.
5. Attempt at most one new fix per run by default. The fix agent can propose a complete replacement for an explicitly allowlisted Markdown file. It can decline when evidence is insufficient. Changes pass path, symlink, size, nonempty-content and whitespace checks, then open as **draft PRs**. No automatic merging, repository script execution, or arbitrary code editing. Repository CI and human review remain required.
6. Once a PR is ready for review, tag configured owners if the current head commit has waited 48 hours without a human review. Reviews of old commits, pending reviews, bot reviews and ordinary issue comments do not satisfy review. One reminder per head SHA survives retries through a hidden GitHub comment marker.
7. Persist groups and PR history on an `issue-pilot-state` branch, even after partial failures. Workflow concurrency serializes runs. Stable branches recover a crash after branch creation; existing PRs recover a crash after PR creation. The state branch is the authoritative long-term grouping memory; keep it backed up. Remote PR reconciliation recovers actions for known group IDs, not arbitrary lost semantic history.

Owner routing is explicit in `config.json` using path globs, including a fallback. Replace demo handles with real GitHub users or teams. This implementation does not parse CODEOWNERS automatically. Draft PRs do not receive stale-review reminders until made ready for review.

## Install in a Cookbook fork with live phase telemetry

The parent workspace includes `setup_fork.py` and `site/`. Run setup from that parent directory using an authenticated GitHub CLI or `GH_TOKEN` in the environment:

```sh
python3 setup_fork.py --repo dahrk/openai-cookbook-fork
```

With `--repo`, the script reuses the selected existing fork and refuses to create a replacement if it is unavailable. Without `--repo`, it reuses or creates your `openai-cookbook-demo` fork. It enables issues, snapshots all open upstream issues and imports them with provenance and retry markers. Use `--no-copy-issues` to keep only the local snapshot. GitHub forks do not automatically copy issues. The checkout is depth one, blob-filtered and sparse; root files are available for this worker. Use `git sparse-checkout disable` later for the entire repository.

Setup installs this worker under `cookbook/tools/issue-pilot` and the workflow under `cookbook/.github/workflows/issue-pilot.yml`, then updates target and owner handles. It preserves an existing installation's local edits. Review those files, commit and push them to the fork's default branch to load the workflow. Enable GitHub Actions on the fork if GitHub requires it. The workflow now runs from `tools/issue-pilot`; it is intended to be installed in the fork rather than run from this extracted standalone directory.

Configure these fork secrets through GitHub's secure UI or authenticated CLI:

- `PILOT_GH_TOKEN`: token scoped to the target fork, contents/issues/pull requests read/write. The worker still uses an explicit token for its GitHub side effects.
- `OPENAI_API_KEY`: required only in live mode.
- `PILOT_SITE_BEARER`: service credential for the published owner-private Site, required when connecting telemetry.

Set repository variables `PILOT_SITE_URL` to the published Site origin and `TARGET_REPO` to your fork (the workflow also defaults to `github.repository`). `OPENAI_MODEL` is optional and retains the original `gpt-4.1` default. `PILOT_MODE` defaults to `demo`; dispatch manually with `mode=live` before deciding whether to enable hourly live runs.

For a local socket-connected offline replay:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-telemetry.txt
# Export PILOT_SITE_URL and PILOT_SITE_BEARER securely in your shell.
.venv/bin/python pilot.py demo --phase-delay 4
```

Without `PILOT_SITE_URL`, replay needs only the Python standard library. Every run writes ordered phase events to `artifacts/events.jsonl` even without a Site. With a Site URL, telemetry requires the optional WebSocket dependency and makes an outbound connection. The runner retries disconnects while retaining local events. Dashboard commands are pause, resume and cancel; they apply at the next worker boundary, after any in-flight model/GitHub operation. Cancellation does not undo completed side effects. Events buffered when a process exits may remain only in its artifact log; this is not a persistent background upload daemon.

Local live execution additionally requires `pip install -r requirements.txt`, `GH_TOKEN`, and `OPENAI_API_KEY`:

```sh
.venv/bin/python pilot.py live --repo YOUR_ACCOUNT/openai-cookbook-demo
```

Serialize live local runs yourself; do not run a local writer alongside the workflow. Scheduled runs persist authoritative grouping memory on `issue-pilot-state`. The live worker refuses writes to `openai/openai-cookbook`. The learning phase remembers groups, PRs and review outcomes; this demo does not train models or modify its own implementation.

## Files and verification

- `pilot.py`: SDK agents, GitHub adapter, grouping, reconciliation, fix policy, reminders, report and replay.
- `config.json`: target, owner map, minimum report count, SLA, fix allowlist.
- `seed_demo.py`: idempotent synthetic report seeding on a fork.
- `tests/test_pilot.py`: duplicate intake, remote fix recovery, review thresholds, marker deduplication, owner routing and proposal boundary tests.
- `docs/DEMO.md`: eight-minute speaking and click-through script.
- `docs/PROVENANCE.md`: real Cookbook snapshot provenance and validation scope.

The replay and tests require no API keys. Live semantic quality, model access, GitHub permissions and hosted scheduling require an authenticated integration run. Demo reports use explicit scenario labels; they do not measure the live classifier's accuracy. Issue descriptions are untrusted model input and truncated to 12,000 characters; the fix agent has no tools or secrets in its input. The repository checkout is read as data and no repository-provided code is executed.
