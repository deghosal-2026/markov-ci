# Architecture

## The one-paragraph version

A YAML config declares a state space, transition probabilities, priors, and policy
(PRD [spec/0003](spec/0003-config-format.md)). The loader expands loop-capable states
into attempt-indexed states (`s2#1`, `s3#2`, …) and assembles the canonical absorbing
chain `P = [[Q, R], [0, I]]` — with the `max_attempts` cap removing loop-back edges so
absorption is guaranteed by construction (ADR-0004). The engine executes hops under the
policy gates (budget → cap → confidence), calls an agent adapter for repairs, checks
every proposal against enforced guardrails, applies patches only in an isolated
sandbox, and emits one versioned JSONL event per hop. Telemetry alone can recompute the
matrix, closing the learning loop.

## Module map

```
src/markov_ci/
├── model/       states, step augmentation, assembly, N/B/t/C, Dirichlet CIs   (F1–F3)
├── policy/      budget → cap → confidence gates                                (F4)
├── triage/      JUnit/log → failure category; log minimizer (≤200 lines)       (F5)
├── agents/      AgentAdapter protocol · SimulatedAgent · harness adapters      (F6, F19)
├── guardrails/  path allowlist · TMR checker · branch isolation · no-auto-merge (F7)
├── engine/      governed loop · sandbox apply-and-test · RunResult             (F8)
├── telemetry/   JSONL event emission · recompute                                (F9, F21)
├── queueing/    Erlang-C (M/M/c) · discrete-event simulator                    (F16)
├── config/      pydantic-validated YAML loader                                  (F1)
├── data/        packaged default state space + priors                           (F11)
└── cli/         typer app: validate · analyze · run · simulate · queue · recompute (F10)
```

## Data flow (one governed run)

```
            ┌─────────────┐
 junit/log ─▶│   triage    │─ category ─┐
            └─────────────┘            ▼
            ┌──────────────────────────────────┐
  config ──▶│ model.assemble(category, adapter) │─▶ P = [[Q,R],[0,I]]
            └──────────────────────────────────┘            │
                                                              ▼
   ┌──────────────── policy gates: budget → cap → confidence ────────────────┐
   │            pass                        fail → a2/a3 (recorded)           │
   ▼                                                                        │
 agents.repair(ctx) ─▶ guardrails.check ─▶ sandbox.apply_and_test ─▶ next hop  │
   ▲                    deny → a2            pass → s4 → a1 | a2              │
   └────────── fail → s2#(k+1) or a2 ◀────────────────────────────────────────┘
 every hop ─▶ telemetry.emit(JSONL event, adapter + category + attempt on board)
```

## Key invariants (test-enforced)

1. **Markov-correct by construction** — attempt history lives in state names, never
   hidden counters (ADR-0002); all closed-form math is exact.
2. **Absorption guaranteed** — caps remove loop edges; even `success=[1,1,1]` priors
   terminate (property test).
3. **Guardrails are code** — allowlist/TMR/branch rules enforced in the engine; the
   always-denied set cannot be widened by config; no force-push code path exists.
4. **Telemetry is a contract** — events alone recompute the matrix; no secrets ever.
5. **Offline-first** — core imports with zero LLM/harness SDKs; demos need no keys.

## Repository layout

```
docs/        OVERVIEW · prd/ (15 sub-PRDs) · spec/ (12 contracts) · adr/ (7) · WBS · tutorials · how-to · reference · explanations
examples/    01-lint-error · 02-unit-assertion-decay · 03-infra-timeout · 04-runner-pool-sizing · 05-github-actions-e2e
schemas/     transition-event.schema.json (telemetry single source of truth)
tests/       unit/ · integration/ · e2e/ · fixtures/
```

Dependency direction: `cli → engine → {model, policy, triage, agents, guardrails,
telemetry}` — `model` depends on nothing but numpy; `queueing` is standalone.
