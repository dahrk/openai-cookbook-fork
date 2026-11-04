# Codex CLI and Agents API comparison

Both adapters use GPT-6 Luna, low reasoning, the same evidence and output schemas, and no model tools or subagents. The CLI runs as a subprocess in GitHub Actions, chosen for easily accessible compute. Agents API runs the managed Codex harness at OpenAI, with no execution environment; Actions retains dispatch and bounded GitHub effects. Neither live path uses the Agents SDK.

## Measurements

- Request time: caller time until the validated structured decision is returned. CLI subprocess startup and Agents API session cleanup are included. API timings additionally distinguish first stream event, first text and completed turn; a first event is not a token.
- Path time: `pilot.live` entry through its terminal event, including all model decisions and local fixture effects.
- Hosted integration time: the real Actions job and worker step, with real GitHub effects and Site telemetry, reported separately.

The controlled benchmark runs implementation, focused review, direct human review and won’t implement. The same tiny README, report, patch and file policy are used; results record the fixture SHA-256. Effects are local fixtures, not real GitHub writes. Direct escape hatches make no model requests. The suite is serial on one `ubuntu-slim` runner (one CPU, 5 GB), with a ten-minute job limit and three-day artifacts. One repetition gives a smoke comparison, not a latency distribution or p95 claim. The CLI runs first, so cache/order effects are possible. The two harnesses have different base instructions, which this comparison does not try to equalize.

## Reproduce

Run the **Issue Pilot runtime benchmark** workflow, or locally with the existing API key in the environment and Codex CLI 0.166.0 installed:

```sh
python benchmark.py --backend both --repetitions 1 --output benchmark-results
```

No GitHub or Site credential is required for the controlled suite. `results.json` includes all outcomes, phase paths, request timings and fixture effects. A failed path fails the benchmark job and preserves partial results. A separate normal issue using each backend verifies real Github/Actions/Site integration.

Official references: [runtime comparison](https://developers.openai.com/api/docs/guides/agents), [Agents API configuration](https://developers.openai.com/api/docs/guides/agents-api/configuration), [stream completion rules](https://developers.openai.com/api/docs/guides/agents-api/sessions/events).

## Results · 4 November 2026

Measured source: `d176462806cefcd6420bb7781322c37d37b4b38a`, on branch `issue-pilot/agents-api`. [Benchmark run 41915693937](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41915693937) succeeded on one `ubuntu-slim` runner. The artifact digest is `730b6bbb40bcb87ce4974d9bfdc0f9d0d2c764190ab790a15a92568cf35395b5` and the fixture digest is `47be28e9aab48a19dffdbff529110eec8b0170642036f1017785d9eba2b392ac`.

| Controlled path | Codex CLI | Agents API | Result in both |
|---|---:|---:|---|
| Implement (classification + fix) | 9.359s | 17.613s | Fixture draft PR, then human feedback |
| Focused review | 3.029s | 7.571s | Fixture COMMENT review, then human feedback |
| Direct human feedback | <1ms | <1ms | Issue remains open; zero model requests |
| Won’t implement | <1ms | <1ms | Fixture issue closes not_planned; zero model requests |

The sub-millisecond escape-hatch times reflect local fixture effects, not GitHub network latency. All eight paths reached their expected terminal state. Six model requests ran: classification, fix and review for each runtime. No benchmark fixture was sent to the production Site.

| Structured decision | Codex CLI caller time | Agents API caller time | API completed-turn time, before cleanup |
|---|---:|---:|---:|
| Classify | 6.473s | 7.995s | 6.179s |
| Fix | 2.880s | 9.336s | 6.941s |
| Review | 3.027s | 7.570s | 5.716s |

API first text appeared at 3.798s, 4.043s and 3.749s respectively. First stream events arrived earlier but are not first-token measurements. CLI first-token timing was not instrumented. Provider token usage was not present in the captured completion event, so no measured token-cost claim is made.

## Real GitHub → runtime → GitHub → Site review

Both normal issue workflows reviewed the full README patch in PR #5 at exact head `ff09219d74b453005fc5dbc0f53d7461b9204050`, with identical review focus. Both published new advisory COMMENT reviews, found zero concrete defects and retained the issue for human feedback. Neither approved, edited or merged the PR. Both terminal events were acknowledged by the Site.

| Measurement | CLI: issue #8 | Agents API: issue #7 |
|---|---:|---:|
| Model request, including adapter overhead | 10.477s | 8.280s |
| Worker step, including GitHub calls and telemetry | 17s | 14s |
| Actions job, excluding queue time | 101s | 43s |
| Node setup + CLI installation | 30s | Skipped |

- [CLI run 41916961472](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41916961472), [review 5776150744](https://github.com/dahrk/openai-cookbook-fork/pull/5#pullrequestreview-5776150744), Site `gh-41916961472-1`.
- [Agents API run 41916297645](https://github.com/dahrk/openai-cookbook-fork/actions/runs/41916297645), [review 5776082125](https://github.com/dahrk/openai-cookbook-fork/pull/5#pullrequestreview-5776082125), Site `gh-41916297645-1`. API first event 0.481s, first text 4.146s, root turn complete 5.948s; remaining caller time includes session cleanup.

The actual review ordering differs from the small fixture: API was faster on the full README, while CLI was faster on the fixture. These are single sequential samples with variable cold setup, caches, provider load and generated output. They do not establish a general latency winner. Python setup also differed (24s CLI, 16s API). The job-time difference is not a pure inference comparison. Live Agents API implementation with a real new PR was not benchmarked; its full orchestration was covered by live inference with fixture GitHub effects. Existing CLI draft PR creation and both real review paths are separately verified.

Raw controlled results and both live review artifacts are preserved locally under `benchmark-results/`. The checked-in summary JSON retains timings and provenance after the three-day Actions artifacts expire. Future comparisons can use up to three repetitions, with alternating runtime order, while remaining serial.
