# Eight-minute Issue Pilot presentation

Open [the local presentation](presentation/index.html) in a browser. It works directly from disk, with no build, server, credentials, or model calls. Use the arrow keys to move, **N** for speaker notes, and **F** for fullscreen. Slide 2 includes a labeled illustrative replay with manual stepping. It never launches a worker or writes to the Site.

The presentation is also linked from the Site at [Presentation](https://issue-pilot-loop-observatory.awaresun14.chatgpt.site/presentation). Its **Image view** opens a time-stamped SVG snapshot of actual state.

The deployed dashboard is [Issue Pilot](https://issue-pilot-loop-observatory.awaresun14.chatgpt.site). Work starts through [the GitHub Issue Pilot form](https://github.com/dahrk/openai-cookbook-fork/issues/new/choose). Existing run history is the dependable demonstration if a new job is queued, finishes too quickly, or the network fails. See [the visual review](PRESENTATION_REVIEW.md) and [the escape-hatch reference](../../ESCAPE_HATCHES.md).

## Demo cast

- **Working agent:** launch a new issue during the talk to show current activity. The completed issue #4 demonstrates a working implementation path through draft PR #5. A finite worker will not stay running after completion.
- **Won’t implement:** issue #3 and Site run `gh-41814426276-1`.
- **Waiting for human feedback:** issue #4, run `gh-41864557130-2`, with [draft PR #5](https://github.com/dahrk/openai-cookbook-fork/pull/5), plus the specific reviewer, issue #6, run `gh-41904870179-1`, whose [advisory review](https://github.com/dahrk/openai-cookbook-fork/pull/5#pullrequestreview-5775139782) checks that exact patch and awaits human feedback. Issue #2 remains available as a direct stop without inference. These workers have stopped and consume no ongoing model inference.
- **Graph and image:** use the live dashboard for movement and selected traveled paths. **Image view** captures current state, including a recent reviewer and an implementation example when available and one won’t-implement run. It is a static snapshot, not a live animation.

## Specific review example

Issue #6 asks Luna to check PR #5 for removal of only the empty h3 and redundant whitespace, preserved links and substantive text, unintended README changes, and the heading outline. The agent published a COMMENT review at the exact PR head with zero concrete defects. Its summary explains that the empty level-three heading disappears while the License heading remains level two. It performed static inspection only, with no link requests, code execution or PR CI. It did not approve or merge.

To show a fresh review agent working live, use the issue form’s **Review a pull request with GPT-6 Luna** route, enter PR **5**, and copy the focus above. A new issue makes one new review inference. Retrying issue #6 at the same PR head recovers its existing comment without another model call. The Site’s Review activity exposes both the focus and result.

## Before presenting

1. Sign in to GitHub as `@dahrk` and open the private Site with the authorized ChatGPT account before screen sharing. Share a browser window or tab so unrelated tabs and account details stay out of the presentation.
2. Open the local presentation and the Site in separate tabs. Check the projected colors because browser appearance extensions can change the palette. OAI/OpenAI Sans is a local font preference, with a system fallback.
3. In the Site, expand **Run history**, open **Issue #6**, and verify the `Needs human review` outcome, `Intake → Review → Human feedback` path, review focus and summary in **Activity**, and PR link. Keep **Issue #4** as the implementation example and **Issue #3** as `Won’t implement`.
4. Decide whether to create a new implementation issue during the talk. That spends API usage on GPT-6 Luna and can create one draft README PR. A direct human-review issue exercises the real workflow and telemetry without inference. A won't-implement issue closes that selected issue as not planned.
5. For a live implementation, use a small, specific README-only request grounded in a real omission. Avoid promising a code or notebook edit. The adapter deliberately declines unsupported changes.
6. Keep [Actions](https://github.com/dahrk/openai-cookbook-fork/actions) open as the runner-status reference. Queue and setup time precede worker telemetry, so the Site may correctly show no active agents while Actions is starting.

## Presentation sequence

| Time | Surface | Narration and action |
|---|---|---|
| 0:00–0:45 | Slide 1 | “Cooking with Codex: better examples, one issue at a time.” |
| 0:45–2:00 | Slide 2 | Explain the work stages and terminal exits. Choose **Won’t implement** in the mocked-example selector and step twice to show an Intake → Won’t implement exit; then choose Build a fix or Review a PR for a longer path. Click **Play example** or **Next state**. “This is a local illustration of the visual language. Pulsing dots on the actual Site represent workers with recent heartbeats. A worker can skip stages or stop for review.” |
| 2:00–2:45 | Slide 3 | “Codex CLI runs inside a small GitHub Actions runner using encrypted Actions secrets. Every model request uses GPT-6 Luna, with no fallback. Actions was chosen for easily accessible compute. The default uses the CLI, not Agents SDK. The optional Agents API path hosts the Codex harness at OpenAI and keeps bounded GitHub effects in Python. Sites hosts the relay and dashboard.” |
| 2:45–3:45 | Slide 4 | Explain the form's four routes. “Implementation attempts can produce a draft README fix, then stop for a person. Direct human review keeps the issue open without a model call. Won’t implement closes the selected issue without a model call.” |
| 3:45–5:30 | Slide 5, then GitHub and the Site | Optionally create one issue using the intended route. Show its Actions job, then the Site. “A queued job has not sent a heartbeat yet. Once the worker connects, its dot appears at the current stage.” Select it to inspect its path. If it finishes quickly, switch to history. Avoid waiting on an empty graph for more than about 20 seconds. |
| 5:30–6:45 | Site, **Issue #4**, **Issue #6**, then **Issue #3** | Show the draft fix, then the specific reviewer. “Issue #6 checked the patch against exact criteria and published advisory findings. Zero concrete defects is a valid review result. Both workers stopped for human feedback. Issue #3 ended as Won’t implement and closed as not planned.” Open the review link to show its exact commit and static-validation limits. |
| 6:45–7:30 | Site **Image view**, then slide 5 | Select issue #4 attempt 2 and open Image view. “This image captures the current graph and the two latest human-feedback examples. It is time-stamped, and the live dashboard continues separately.” Show draft PR #5 as the concrete work product. |
| 7:30–8:00 | Slide 6 | Copy the build prompt and substitute your own owner/repository. The plaintext link supports sharing or embedding. Human approval and merging remain in GitHub. |

## If the live moment is awkward

- **No active agents:** Say the worker is idle or Actions is starting. Open Run history. Do not describe old runs as live.
- **The run finishes instantly:** Open its terminal entry. The retained path is the demonstration. Direct escape hatches are intentionally short.
- **The model call is still in progress:** Explain the boundary and move to verified history. Pause/cancel take effect after the current model/GitHub operation, rather than immediately.
- **The Site connection drops:** Use the local illustration on slide 2, explicitly labeled, then the verified record links on slide 5. Do not claim the illustration is live telemetry.
- **No Site MCP tools in the conversation:** Use browser controls. Publication advertises the MCP tools, but an authenticated ChatGPT invocation has not been verified in this session.
- **Someone asks to merge:** Review and merge manually in GitHub. The demo never merges automatically.

## Current stages and boundaries

| Requested stage | Current behavior |
|---|---|
| Schedule | Hourly scheduling is disabled. The legacy workflow name still says “Scheduled Issue Pilot.” |
| Dispatch | Opening/reopening an issue or manual Actions dispatch. Both the actor and issue author must be `@dahrk`. |
| Intake | Reads and validates the selected issue. |
| Triage | Combines Group (Luna matches related reports) and Rank (sort by report count) within one worker. |
| Implement | The raw `propose` phase uses Codex CLI with GPT-6 Luna only, low reasoning, and a README policy. At most one new draft fix per run. |
| Review | An explicit review route uses Luna to inspect a single README-only PR against a focus, publishes COMMENT findings at the exact head, then stops for human feedback. Existing implementation runs also check human reviews and reminders. |
| Approval | A person reviews and merges in GitHub. No automated approval or merge stage. |
| Save outcome | The raw `learn` phase saves group and PR state for later runs; it does not retrain the model. |

The dashed Review → Implement arrow means human feedback followed by a new implementation issue. It is not an automatic review/rework loop. Actual selected paths use recorded events and include terminal outcomes.

Site MCP reads status and requests existing-worker controls. It does not launch workers, execute arbitrary commands, or approve PRs. Browser buttons expose pause, resume, and cancel. MCP also defines human-review and won't-implement controls. Queue/setup time before telemetry is visible in Actions, not as a running dot on the Site.

## Verified records

- [Issue #6 focused review](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41904870179): one real Luna review on `ubuntu-slim`, exact head `ff09219d74b453005fc5dbc0f53d7461b9204050`, zero concrete findings, COMMENT review published, terminal `needs_human_review`. Site path: Intake → Review → Human feedback.


- [Issue #4 successful retry, attempt 2](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41864557130/attempts/2): recovered the existing two-line README fix after enabling the approved repository PR-creation setting, opened [draft PR #5](https://github.com/dahrk/openai-cookbook-fork/pull/5), and stopped for human review. The retry made no new model calls. Attempt 1 remains a useful Failed-state example.


- [Issue #1 Luna attempt, run 41814341953](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41814341953): declined a notebook request outside the README policy and ended as `needs_human_review`.
- [Issue #2 direct review, run 41815507448](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41815507448): ran on `ubuntu-slim`, skipped Codex setup and inference, left the issue open.
- [Issue #3 won't implement, run 41814426276](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41814426276): skipped inference and closed issue #3 as `not_planned`.

## Separate offline report

`python pilot.py demo` and `artifacts/index.html` remain a synthetic fixture replay. They include mock PR #201, simulated clock advances and a simulated merge. They are separate from the live Site demo. Do not use their mock PR or merge as proof of a real GitHub outcome. The live configuration uses Codex CLI, not the older Agents SDK adapter described in previous versions of this script.

## Current presentation and runtime comparison

Slide 2 shows all five terminal states and can replay early exits, failure or cancellation. Clicking a terminal state on the actual dashboard opens filtered history. Slide 4 connects routes to their stops. Slide 5 contains the concrete empty-heading request and real record links. Slide 6 is the reusable prompt, with a tested Copy button and plaintext link.

The runtime comparison is on branch `issue-pilot/agents-api`. `docs/BENCHMARK.md` distinguishes the serial, live-inference fixture suite from actual review workflows. Issues #7 (Agents API) and #8 (CLI) reviewed the same full README patch and focus, each produced a COMMENT review with zero findings, and both stopped for human feedback. Their request timings were 8.280s and 10.477s respectively. The small fixture showed the reverse order; avoid claiming a universal speed winner from one sample. Both used the smallest runner and Luna only.
