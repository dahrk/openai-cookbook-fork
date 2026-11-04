# Issue Pilot

An eight-minute demo of scheduled GitHub issue intake → semantic duplicate grouping → impact ranking → draft fixes → stale-review owner reminders. Uses **GitHub Actions + Codex CLI with GPT-6 Luna only**, with a credential-free replay. Everything runs locally except authenticated GitHub/OpenAI calls.

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

The workflow is installed in `dahrk/openai-cookbook-fork`. It runs on newly opened or reopened issues only when both the issue author and triggering actor are `@dahrk`. Manual dispatch also requires `@dahrk` and an open issue number authored by that account. The worker fetches and rechecks the current issue before model use or closing it. Other authors cannot start a worker using this workflow's secrets. Hourly scheduling is disabled.

Use **Issues → New issue → Issue Pilot**. The form offers:

- **Implement with GPT-6 Luna**: process the selected issue, allow at most one bounded draft README fix, then stop for human review.
- **Needs human review**: leave the issue open and record `needs_human_review` without model inference.
- **Won't implement (close as not planned)**: close only the selected issue with `state_reason=not_planned`, record `wont_implement`, and skip model inference.

Missing form choices default to human review. Manual dispatch accepts `issue_number` and `disposition` (`from_issue`, `implement`, `needs_human_review`, or `wont_implement`). A selected owner-authored issue can request implementation without the duplicate-report threshold. Draft PRs always require a person; no outcome automatically merges them. See the workspace's local `ESCAPE_HATCHES.md` for the demo reference.

1. Read open issues, excluding PRs, with complete API pagination. Issue dispatch reads the selected owner-authored issue. Local batch entry points also filter reports to `@dahrk`; logs and Site telemetry report the processed and total counts. All proposals and state writes target the selected fork. Local `--issue-limit 0` processes every report. Source repository identity is persisted with state to prevent issue-number collisions.
2. Codex CLI structured output compares each new issue with persisted root causes. Confidence below 0.85 makes a separate group. Previously seen issue IDs retain their group.
3. Rank by the cumulative number of distinct issue reports, descending. This demo deliberately treats report count as impact; reactions and severity are not additional weights. Historical reports stay counted after closure. A repeated issue contributes once.
4. Reconcile existing open, closed, and merged PRs using stable per-group branch names. Reuse any prior PR. Closed unmerged PRs require manual intervention rather than automatic reopening.
5. Attempt at most one new fix per run by default. The fix agent can propose a complete replacement for an explicitly allowlisted Markdown file. It can decline when evidence is insufficient. Changes pass path, symlink, size, nonempty-content and whitespace checks, then open as **draft PRs**. No automatic merging, repository script execution, or arbitrary code editing. Repository CI and human review remain required.
6. Once a PR is ready for review, tag configured owners if the current head commit has waited 48 hours without a human review. Reviews of old commits, pending reviews, bot reviews and ordinary issue comments do not satisfy review. One reminder per head SHA survives retries through a hidden GitHub comment marker.
7. Persist groups and PR history on `issue-pilot-state-<issue_number>`, even after partial failures. Runs for one issue serialize; different issues use independent state branches and can run concurrently without replacing one another in a shared pending slot. Stable branches recover a crash after branch creation; existing PRs recover a crash after PR creation. The state branch is the authoritative long-term grouping memory; keep it backed up. Remote PR reconciliation recovers actions for known group IDs, not arbitrary lost semantic history.

Owner routing is explicit in `config.json` using path globs, including a fallback. Replace demo handles with real GitHub users or teams. This implementation does not parse CODEOWNERS automatically. Draft PRs do not receive stale-review reminders until made ready for review.

## Install in a Cookbook fork with live phase telemetry

The parent workspace includes `setup_fork.py` and `site/`. Run setup from that parent directory using an authenticated GitHub CLI or `GH_TOKEN` in the environment:

```sh
python3 setup_fork.py --repo dahrk/openai-cookbook-fork
```

With `--repo`, the script reuses the selected existing fork and refuses to create a replacement if it is unavailable. Without `--repo`, it reuses or creates your `openai-cookbook-demo` fork. It enables issues, snapshots all open upstream issues and imports them with provenance and retry markers. Use `--no-copy-issues` to keep only the local snapshot. GitHub forks do not automatically copy issues. The checkout is depth one, blob-filtered and sparse; root files are available for this worker. Use `git sparse-checkout disable` later for the entire repository.

Setup installs this worker under `cookbook/tools/issue-pilot` and the workflow under `cookbook/.github/workflows/issue-pilot.yml`, then updates target and owner handles. It preserves an existing installation's local edits. Review those files, commit and push them to the fork's default branch to load the workflow. Enable GitHub Actions on the fork if GitHub requires it. The workflow runs from `tools/issue-pilot`; it is intended to be installed in the fork rather than run from this extracted standalone directory.

Configure these fork secrets through GitHub's secure UI or authenticated CLI:

- `OPENAI_API_KEY`: required only for the implementation route.
- `PILOT_SITE_BEARER`: service credential for the published owner-private Site, required when connecting telemetry.

The default runtime is Codex CLI on GitHub Actions: **easily accessible compute** already available beside the issues and PRs. The owner can choose **Agents API (managed Codex)** in the issue form or override `backend` on manual dispatch. Agents API runs the Codex harness and orchestration at OpenAI; Actions still validates issues, dispatches requests, applies bounded GitHub effects and sends Site telemetry. The adapter uses `environment: none`, no tools and no subagents, avoiding an extra sandbox for this text-only demo. Both paths pin `OPENAI_MODEL=gpt-6-luna` and low reasoning; another model is rejected without fallback. Codex CLI is pinned to `0.166.0`. The Site origin is the existing published private Site, and the target is `github.repository`. The workflow uses its own `GITHUB_TOKEN` with contents/issues/pull-request write permissions; no separate GitHub token secret is needed. GitHub repository policy must allow Actions to create pull requests. Credentials are scoped to the steps that need them. The Codex child process receives only its API credential, runs from an isolated temporary directory, and has shell, browser, plugin, and subagent tools disabled. Python retains responsibility for allowlisted draft-PR writes.

No repository variables are required. The runner ID is `gh-<run_id>-<attempt>`, matching the Site's run list. Required telemetry fails the workflow if the Site does not acknowledge the initial or terminal events. The user approved configuring both encrypted Actions secrets. Do not store credential values in source or artifacts. There is no separate GitHub token secret: the workflow uses its scoped `GITHUB_TOKEN`.

To run live, create an Issue Pilot issue as `@dahrk`, choose the form outcome, and submit. To retry an existing issue, choose **Actions → Scheduled Issue Pilot → Run workflow**, enter the open owner-authored issue number, and select `implement`. The Site lists the run as `gh-<run_id>-<attempt>`. Its main view emphasizes active workers; outcome filters expose parked and closed runs with their ordered phase history.

For a local socket-connected offline replay:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-telemetry.txt
# Export PILOT_SITE_URL and PILOT_SITE_BEARER securely in your shell.
.venv/bin/python pilot.py demo --phase-delay 4
```

Without `PILOT_SITE_URL`, replay needs only the Python standard library. Every run writes ordered phase events to `artifacts/events.jsonl` even without a Site. With a Site URL, telemetry requires the optional WebSocket dependency and makes an outbound connection. The runner retries disconnects while retaining local events. Dashboard commands are pause, resume and cancel; they apply at the next worker boundary, after any in-flight model/GitHub operation. Cancellation does not undo completed side effects. Events buffered when a process exits may remain only in its artifact log; this is not a persistent background upload daemon.

Local live execution requires `npm install -g @openai/codex@0.166.0`, the telemetry dependency when using the Site, `GH_TOKEN`, and `OPENAI_API_KEY`:

```sh
.venv/bin/python pilot.py live --repo dahrk/openai-cookbook-fork --issue-number YOUR_ISSUE_NUMBER --disposition implement
```

Serialize live local runs yourself; do not run a local writer alongside the workflow. Issue-triggered runs persist authoritative memory on their per-issue state branch. The live worker refuses writes to `openai/openai-cookbook`. The learning phase remembers groups, PRs and review outcomes; this demo does not train models or modify its own implementation.

## Files and verification

- `pilot.py`: GitHub adapter, grouping, reconciliation, fix policy, reminders, report and replay.
- `codex_brain.py`: Luna-only Codex CLI backend and strict structured-output schemas.
- `agents_api_brain.py`: the managed Agents API backend, selected with `PILOT_BACKEND=agents_api`.
- `benchmark.py`: matched live-inference path comparison with isolated GitHub effects; see [benchmark methodology](docs/BENCHMARK.md).
- `PILOT_BACKEND=agents`: optional legacy Agents SDK backend, also restricted to GPT-6 Luna; install `requirements.txt` only for that backend.
- `config.json`: target, owner map, minimum report count, SLA, fix allowlist.
- `seed_demo.py`: idempotent synthetic report seeding on a fork.
- `tests/test_pilot.py`: duplicate intake, remote fix recovery, review thresholds, marker deduplication, owner routing and proposal boundary tests.
- `docs/DEMO.md`: eight-minute speaking and click-through script.
- `docs/PROVENANCE.md`: real Cookbook snapshot provenance and validation scope.

The replay and tests require no API keys. Live semantic quality, model access, GitHub permissions and hosted scheduling require an authenticated integration run. Demo reports use explicit scenario labels; they do not measure the live classifier's accuracy. Issue descriptions are untrusted model input and truncated to 12,000 characters; the fix agent has no tools or secrets in its input. The repository checkout is read as data and no repository-provided code is executed.

The demo uses `ubuntu-slim` (one CPU, 5 GB RAM), a ten-minute timeout, a sparse checkout of the worker, and three-day artifact retention. Human-review and won't-implement routes skip Node/Codex installation and do not receive the API key.

## Focused agent review

Use the Issue Pilot form outcome **Review a pull request with GPT-6 Luna**, with a **Pull request number** and **Review focus**. Manual dispatch also accepts `review`, using those fields from the issue. Only `@dahrk` can trigger it. The route reads one README-only PR within the fork, gives the exact base/head content and patch to Luna, and publishes advisory findings as a COMMENT review at that head. It refuses a changed head and then stops for human feedback. It never approves, merges, runs repository code or edits the patch. Retries reuse the bot review for that issue and head. Both review and implementation require the encrypted API secret; direct human review and won’t implement do not.

## Runtime comparison

Codex CLI, Agents SDK and Agents API are different integrations. The live default uses the CLI, not the Agents SDK. The optional SDK adapter remains for local implementation experiments; it is not what the deployed workflow executes. The Agents API variant calls `/v1/agents/sessions` over HTTPS and collects the completed root-turn result. It does not dispatch a Codex Cloud UI task.

Request timings are stored in `artifacts/request-metrics.jsonl` without prompts, outputs or credentials. Use **Actions → Issue Pilot runtime benchmark → Run workflow** for one serial comparison of implementation, focused review and both escape hatches. The benchmark uses real Luna inference and the actual `pilot.live` orchestration with fixture GitHub writes and no Site connection; it does not create benchmark PRs or close real issues. Live integration runs are reported separately.
