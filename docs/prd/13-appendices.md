# 13 — Appendices

## Appendix A — Glossary

- **Transient state** — a state the run can leave (verify, triage, agent, worktree validation, regression).
- **Absorbing state** — terminal; once entered, never left (`a1`, `a2`, `a3`).
- **Fundamental matrix** — `N = (I−Q)⁻¹`; expected visits to each transient state.
- **Absorption probability** — `B = N·R`; chance of ending in each absorbing state.
- **Step-augmented state** — attempt index encoded in the state name (`s2#2`), keeping the
  chain Markov while modeling per-attempt decay.
- **Prior vs empirical** — cold-start probabilities (shipped) vs telemetry-derived
  (recomputed); config labels which is in force.
- **TMR** — test-modification-ratio: test lines changed ÷ src lines changed; > 1.0 flags
  possible test weakening.
- **DES** — discrete-event simulator (runner-pool queueing beyond M/M/c assumptions).
- **Harness** — a coding-agent runtime (Claude Code, OpenCode, Aider, …) invoked headless.
- **Adapter tiers** — T1 protocol-conformant, T2 verified harness template, T3 BYO command.

## Appendix B — CUJ ↔ feature ↔ WBS traceability matrix

| Feature | Size | Depends on | CUJs | ADR | WBS tickets | Issues |
|---|---|---|---|---|---|---|
| F1 state-space config | M | — | 1 | [0002](../adr/0002-step-augmented-states.md), [0006](../adr/0006-src-layout-strict-typing.md) | M1.1–M1.2, M2.2–M2.3 | #7, #8, #16, #17 |
| F2 assembly + validation | M | F1 | 1, 3 | [0001](../adr/0001-absorbing-markov-model.md), [0002](../adr/0002-step-augmented-states.md), [0004](../adr/0004-hard-caps-guarantee-absorption.md) | M1.3–M1.4 | #9, #10 |
| F3 forecast math | M | F2 | 1, 5 | [0001](../adr/0001-absorbing-markov-model.md) | M1.5–M1.7 | #11, #12, #13 |
| F4 policy engine | S | F2 | 1, 3 | [0004](../adr/0004-hard-caps-guarantee-absorption.md) | M2.1 | #15 |
| F5 deterministic triage | M | — | 2 | [0008](../adr/0008-deterministic-triage-before-agents.md) | M3.1–M3.3 | #19, #20, #21 |
| F6 adapter protocol + simulated agent | M | F5 | 2, 4 | [0003](../adr/0003-simulated-agent-default.md) | M4.1–M4.2 | #22, #23 |
| F7 guardrails | M | — | 2, 6 | [0009](../adr/0009-guardrails-enforced-in-code.md) | M5.1–M5.3 | #26, #27, #28 |
| F8 runtime engine | L | F2, F4, F5, F6, F7 | 2, 3 | [0001](../adr/0001-absorbing-markov-model.md), [0004](../adr/0004-hard-caps-guarantee-absorption.md) | M6.1–M6.4 | #29, #30, #31, #32 |
| F9 telemetry contract | S | F8 | 3, 4, 5 | [0005](../adr/0005-telemetry-versioned-contract.md) | M6.1, M6.5, M8.2 | #29, #33, #38 |
| F10 CLI surface | S | F3 | all | [0006](../adr/0006-src-layout-strict-typing.md) | M2.4, M6.4 | #18, #32 |
| F11 packaged defaults | S | F1 | 1 | — | M2.3 | #17 |
| F12 documentation set | M | F10 | 1, 4 | [0006](../adr/0006-src-layout-strict-typing.md) | M8.3 | #39 |
| F13 offline proof-suite demos | M | F6, F8 | 4 | [0003](../adr/0003-simulated-agent-default.md) | M9.1–M9.3, M9.7–M9.8 | #41, #42, #43, #62, #63 |
| F14 self-hosted CI | S | F10, F13 | 3 | — | M0.4 | #4 |
| F15 GitHub Action | S | F10 | 1 | — | M10.1 | #46 |
| F16 queueing module | M | — | 3 | [0010](../adr/0010-dual-queueing-model.md) | M7.1–M7.3 | #34, #35, #36 |
| F17 Monte-Carlo simulate | S | F3 | 1, 5 | — | M8.1 | #37 |
| F18 demos 04–05 | M | F16, F15 | 3 | [0010](../adr/0010-dual-queueing-model.md) | M9.4–M9.5 | #44, #45 |
| F19 harness adapters | M | F6 | 4 | [0007](../adr/0007-harness-adapters-not-raw-sdks.md), [0011](../adr/0011-local-llms-via-openai-compatible-endpoints.md) | M4.3–M4.5 | #24, #25, #64 |
| F20 GitLab/Jenkins how-tos | S | F10 | 1 | — | M8.4 | #40 |
| F21 recompute pipeline | M | F9 | 4, 5 | [0005](../adr/0005-telemetry-versioned-contract.md) | M8.2 | #38 |
| F22 property-based hardening | M | F3, F5, F7 | 2, 6 | [0004](../adr/0004-hard-caps-guarantee-absorption.md) | M1.8 | #14 |
| F23 cost model in currency | M | F3 | 5 | — | M11.1 | #53 |
| F24 A/B policy comparison | S | F3 | 5 | — | M11.2 | #54 |
| F25 state-space visualization | S | F3 | 5 | — | M11.3 | #55 |
| F26 multi-pipeline aggregation | L | F21 | 5 | — | M11.4 | #56 |
| F27 time-varying matrices / drift | M | F21 | 5 | — | M11.5 | #57 |
| F28 community harness adapters | S | F19 | 4 | [0007](../adr/0007-harness-adapters-not-raw-sdks.md) | M11.6 | #58 |
| F29 MCP governance server | M | F3, F16 | 4 | [0007](../adr/0007-harness-adapters-not-raw-sdks.md) | M11.7 | #59 |

**Size key** (single-maintainer relative effort): S ≤ days · M ≤ 1–2 weeks · L > 2 weeks.
**Depends on** = hard build-order edges; the WBS sequence already respects them.
**ADR** = the decision record(s) that bind the feature; `—` means no ADR is required
(the feature follows an existing principle or is pure packaging/integration).
**Issues** = GitHub issue numbers; the canonical `#NN` ↔ `M<n>.<t>` map lives in
[../WBS.md](../WBS.md).

## Appendix C — Spec contract map

| Contract | Implements |
|---|---|
| [spec/0001 state model](../spec/0001-state-model.md) | F1 |
| [spec/0002 matrix assembly](../spec/0002-matrix-assembly.md) | F2, F3 |
| [spec/0003 config format](../spec/0003-config-format.md) | F1, F11 |
| [spec/0004 policy engine](../spec/0004-policy-engine.md) | F4 |
| [spec/0005 guardrails](../spec/0005-guardrails.md) | F7 |
| [spec/0006 agent adapters](../spec/0006-agent-adapters.md) | F6, F19 |
| [spec/0007 telemetry events](../spec/0007-telemetry-events.md) | F9 |
| [spec/0008 CLI contract](../spec/0008-cli-contract.md) | F10, F16, F17, F21 (command + exit-code contracts) |
| [spec/0009 queueing](../spec/0009-queueing.md) | F16 |
| [spec/0010 triage](../spec/0010-triage.md) | F5 |
| [spec/0011 engine runtime](../spec/0011-engine-runtime.md) | F8 |
| [spec/0012 engineering baseline](../spec/0012-engineering-baseline.md) | F12, F14, F22, quality attributes |

**Features without a dedicated spec contract (by design):**

| Feature | Where it is governed instead |
|---|---|
| F13, F18 (demos) | [docs/tutorials/](../tutorials/01-lint-error-first-pass.md) — examples, not contracts; must match shipped behaviour |
| F15 (GitHub Action), F20 (GitLab/Jenkins) | [docs/how-to/](../how-to/integrate-github-actions.md) — integration contract; exit codes per spec/0008 |
| F23–F29 (v0.3 live ops) | Not yet contracted — each gets a `spec/00NN-*.md` when its ticket starts |
