# 11 — Risks, competitive landscape, open questions

## 1. Risk register

| Risk | Sev | Likelihood | Mitigation |
|---|---|---|---|
| Cold-start: adopters have no telemetry | High | High | Conservative priors + Dirichlet CIs; priors clearly labeled `source: prior` in config |
| Harness-dependent probabilities — same model varied ~70× in tokens across harnesses | Med | High | Priors keyed by category × adapter; `adapter` on every event; per-harness `recompute` |
| Harness CLI churn breaks T2 templates | Med | Med | Version pinning + tolerance policy (07 §4.6); T3 BYO adapter absorbs breakage; community templates (F28) |
| Memorylessness mismatch (history matters) | Med | Med | Step-augmented states (ADR-0002) — model stays Markov-correct by construction |
| Docs/code drift after contract-first writing | Med | Med | Docs-are-tests CI job; reference pages generated against schema files |
| Scope creep toward harness | High | Med | Non-goals (03 §6); thin protocol; WON'T list enforced in review |
| Test-weakening agents in the wild | High | Med | TMR hard stop; mandatory-review flag; documented as anti-pattern #1 |
| PyPI name conflict | Low | Low | Check before M10; fallback `markov-ci-core` |
| Single-maintainer bus factor | Med | Med | Docs-as-onboarding, clean module ownership, contributing guide from M0 |

## 2. Competitive landscape

| Category | Examples | What they do | Why markov-ci differs |
|---|---|---|---|
| Retry actions | nick-fields/retry & similar | Blind re-run N times | Probability model, cost forecast, escalation semantics, absorption guarantee |
| Agent harnesses in CI | Claude Code CI, Aider, Devin-style runners | Act, generate patches | No governance model: no forecasts, no budgets, no test-integrity checks |
| Automated program repair (APR) | Classical: GenProg, TravisRepair · LLM-era: SWE-bench repair agents | Generate fixes for failing tests/builds | APR *is* an agent by our definition — it can run as a T1/T3 adapter. markov-ci governs whoever fixes: forecasts spend, caps loops, protects tests. APR's probabilistic fix quality is exactly what the matrix models |
| CI observability | Datadog CI Visibility, CircleCI insights | Measure pipeline health, flakiness, duration | They observe pipelines; they neither govern agents nor forecast agentic spend — though their data is excellent triage input |
| Prompt/output guardrails | guardrails-ai, instructor | Validate LLM text | Pipeline-level state machine + runner economics, not text validation |
| Flaky-test management | Trunk, BuildPulse | Detect/rerun flakes | Deterministic triage is one input here; flakes route away from agents entirely |
| Orchestration engines | Temporal, Prefect | Durable execution graphs | Deterministic retry semantics; no absorbing-chain math, no agent economics |
| Erlang-C calculators | Web tools | Queue math | CI-aware, composable, burst-simulation included |
| CI MCP servers | CircleCI, Buildkite, Semaphore, TeamCity | Expose pipeline data/ops to agents as tools | Data exposure, not governance: no budgets, forecasts, or absorption guarantees |

**Differentiation in one line:** the only tool that computes what your agents will
cost, proves they can't run away, and keeps humans accountable for merges.

## 3. Open questions

1. PyPI availability for `markov-ci` (verify before M10.2).
2. ~~Adapter packaging~~ — **resolved 2026-11-16:** harness adapters as extras
   (`markov-ci[harness]`) + generic BYO-command; raw SDKs not wrapped in core.
3. Public flip timing vs articles 1–2 (articles must link a public repo; current plan:
   flip first, then publish — confirm at the release gate).
4. Should `a3_budget_exceeded` events feed an org-level budget ledger? (v0.3 question)
5. Do we need Windows runner support in demos? (Linux/macOS first)
