# Snapshot and verification

Source: https://github.com/openai/openai-cookbook

Shallow sparse checkout obtained during implementation. Commit: `f5819076643583e2c2a77268e7fe522e927499d0`.

`fixtures/cookbook-README.md` and `fixtures/cookbook-LICENSE` preserve the README and MIT license from that commit. No upstream issue or pull request was created. All seven report fixtures are synthetic and labeled accordingly. The sample diff adds a section explicitly scoped to the synthetic demo, rather than asserting an established upstream defect.

Verification performed locally:

- Offline scenario replay, including repeat intake, PR reuse, merged-fix memory and reminder deduplication.
- Python unit tests for grouping and effect reconciliation, review SLA edge cases, owner routing, comment idempotency and file/symlink boundaries.
- Agents SDK 0.24.0 installation and construction of both structured-output agents, without API calls.
- `git apply --check` of the replay patch against the real shallow Cookbook checkout.

Not verified without credentials: live model classifications and generated fixes, authenticated issue/branch/PR/comment writes, hosted Actions execution or real scheduled delivery. The workflow is provided as source and defaults to mock mode until explicitly configured.
