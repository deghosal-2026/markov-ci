# markov-ci

**Markov-governed, self-healing CI/CD.**

`markov-ci` is a reusable framework for orchestrating non-deterministic CI/CD
pipelines — including pipelines with autonomous AI agents in the loop — as
**absorbing Markov chains**.

Instead of hardcoding brittle `if/else` retry rules around probabilistic
agents, you define a state space, empirical transition probabilities, and hard
absorbing boundaries (ready-for-human-review, escalate-to-author,
budget-exceeded). From that, `markov-ci` computes:

- Expected state visits, steps, and cost before absorption (`N = (I − Q)⁻¹`)
- Absorption probabilities per outcome (`B = N·R`)
- Confidence-threshold and budget guardrails that make runaway agent loops
  mathematically impossible

## Status

**Pre-alpha.** Private during initial development; intended to be released as
open source under Apache-2.0.

## Roadmap

- [ ] Core engine: state space, transition matrix, fundamental-matrix math
- [ ] Deterministic failure triage (JUnit XML / log classification)
- [ ] Policy engine: probability thresholds, step caps, token/wall-clock budgets
- [ ] Pluggable agent adapters (offline simulated agent + real LLM adapter)
- [ ] Guardrails: enforced least-privilege, test-modification-ratio checker
- [ ] Runner-fleet sizing: M/M/c queueing + discrete-event simulation
- [ ] Telemetry schema + transition-matrix recompute from production data
- [ ] Working demos, docs, and a composite GitHub Action

## License

Apache-2.0. See [LICENSE](LICENSE).
