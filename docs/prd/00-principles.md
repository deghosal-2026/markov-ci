# 00 — Product principles

These ten principles bind every product decision in this PRD. When a feature proposal
conflicts with a principle, the principle wins — or the principle is changed first,
visibly, via an ADR. (Engineering-binding versions of the same ideas live in
[../spec/README.md](../spec/README.md); the ADRs record when each was chosen.)

1. **Markov-correct by construction.** Every matrix the engine executes is a true
   homogeneous Markov chain; attempt history lives in the state name, never in hidden
   counters. The math is exact, not approximate.
2. **Absorption guaranteed.** Hard caps make runaway loops mathematically impossible —
   termination is structural, not procedural.
3. **Guardrails are code.** Allowlists, TMR checks, branch isolation, no-auto-merge are
   enforced in the engine. A guardrail that exists only as a comment does not exist.
4. **Offline-first.** Every demo, test, and first-run experience works with zero API
   keys and zero network. Real agents are opt-in extras.
5. **Determinism before intelligence.** Nothing reaches an agent before a deterministic
   classifier has categorized it; infra flakes never spend tokens.
6. **Telemetry is a contract.** Events are schema-versioned JSON; the matrix is
   recomputable from events alone, per category and per adapter.
7. **Governance is never delegated.** A harness's own allowlists or safety settings are
   additive defense, never a substitute for markov-ci's.
8. **Humans merge.** `a1_ready_for_human_review` is terminal by design. Agents accelerate
   the path to green; people stay accountable for what ships.
9. **No phoning home.** Telemetry is local, user-owned, user-shipped. Centralized
   collection would be a trust breach of the product's own promise.
10. **Forecast before you govern.** `analyze` before `run` — the adoption ladder
    (12 §6) is this principle operationalized.
