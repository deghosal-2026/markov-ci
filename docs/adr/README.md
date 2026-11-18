# Architecture Decision Records (ADR)

One decision per file, numbered in decision order (MADR-lite format). ADRs are immutable
once accepted — supersede with a new ADR, never edit history. To add one: copy
[template.md](template.md), take the next number, open a PR. Every ADR records
**Deciders**, a **PR** link, **Decision Drivers**, and **≥ 2 real Considered Options**
(with why each lost) — a single-option ADR is not a decision.

**Spec ↔ ADR drift.** Where a spec diverges from an accepted ADR, the spec records it in
its `Amends:` field and the ADR gains an `Amended by:` line (e.g. spec 0005 §1 ↔
ADR-0009; spec 0011 §2 ↔ ADR-0012). Accepted ADRs are never edited in place — supersede
with a new ADR (e.g. ADR-0016 over ADR-0007's shell composition).

| # | Decision | Status |
|---|---|---|
| [0001](0001-absorbing-markov-model.md) | Model pipelines as absorbing Markov chains | Accepted |
| [0002](0002-step-augmented-states.md) | Encode attempt count in the state name | Accepted |
| [0003](0003-simulated-agent-default.md) | Offline simulated agent is the default adapter | Accepted |
| [0004](0004-hard-caps-guarantee-absorption.md) | Caps make every assembled chain acyclic (nilpotent `Q`) | Accepted |
| [0005](0005-telemetry-versioned-contract.md) | Telemetry is a schema-versioned JSONL contract | Accepted |
| [0006](0006-src-layout-strict-typing.md) | src/ layout, `py.typed`, `mypy --strict` | Accepted |
| [0007](0007-harness-adapters-not-raw-sdks.md) | Real agents via headless harness CLIs, never raw SDKs | Accepted (invocation amended by ADR-0016) |
| [0008](0008-deterministic-triage-before-agents.md) | Deterministic triage before any agent runs | Accepted |
| [0009](0009-guardrails-enforced-in-code.md) | Guardrails are enforced in code, never delegated | Accepted |
| [0010](0010-dual-queueing-model.md) | Dual queueing model: Erlang-C estimate + DES | Accepted |
| [0011](0011-local-llms-via-openai-compatible-endpoints.md) | Local LLMs via OpenAI-compatible endpoints, never a new SDK | Accepted |
| [0012](0012-execution-isolation.md) | Validation runs in a disposable, resource-bounded copy | Accepted |
| [0013](0013-trust-boundary.md) | Untrusted input never crosses into the host | Accepted |
| [0014](0014-markov-planned-not-governed.md) | "Markov-governed" means a planning model governing a bounded runtime | Accepted |
| [0015](0015-estimation-and-learning.md) | Estimation and learning — smoothed per-attempt curves, honest about censoring | Accepted |
| [0016](0016-argv-only-harness-invocation.md) | Harness invocation is argv-only — the prompt is never a shell string | Accepted |
| [0017](0017-exit-code-contract.md) | Exit codes are the outcome contract — a2 moves off Click's reserved 2 | Accepted |

**ADR-20 contradiction table.** The v0.1.1 review found eleven ADR↔ADR / ADR↔spec
contradictions; each is resolved here by an amendment marker or a corrected ADR, never by
editing a decision: ADR-0007↔ADR-0011 (amended), ADR-0004 target state + runtime bound
(restated), ADR-0002/spec 0004 runtime counter (noted), ADR-0009 threshold (fixed at 1.0),
ADR-0008 `unknown` prior + routed-away data (noted), ADR-0005 schema sufficiency (amended
by spec 0007 §4), ADR-0001 75/15/10 (labelled uncited), ADR-0011 "literally true" (fixed).
