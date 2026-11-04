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
