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
- [ ] Pluggable agent adapters — offline simulated agent + headless harness adapters (Claude Code, OpenCode, Aider) + bring-your-own-command
- [ ] Guardrails: enforced least-privilege, test-modification-ratio checker
- [ ] Runner-fleet sizing: M/M/c queueing + discrete-event simulation
- [ ] Telemetry schema + transition-matrix recompute from production data
- [ ] Working demos, docs, and a composite GitHub Action

## Documentation

- [What & why — start here](docs/OVERVIEW.md)
- [Product requirements (PRD)](docs/prd/README.md) · [Technical contracts (spec)](docs/spec/README.md) · [Decision records (ADR)](docs/adr/README.md) · [Work breakdown (WBS)](docs/WBS.md)
- Quick start, tutorials, how-tos, and reference live in [docs/](docs/) — `mkdocs serve` builds the site.

## License

Apache-2.0. See [LICENSE](LICENSE).
