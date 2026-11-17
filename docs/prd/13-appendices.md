# 13 — Appendices

## Appendix A — Glossary

- **Transient state** — a state the run can leave (verify, triage, agent, sandbox, regression).
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

| Feature | CUJs | WBS tickets |
|---|---|---|
| F1 state-space config | 1 | M1.1–M1.2, M2.2–M2.3 |
| F2 assembly + validation | 1, 3 | M1.3–M1.4 |
| F3 forecast math | 1, 5 | M1.5–M1.7 |
| F4 policy engine | 1, 3 | M2.1 |
| F5 deterministic triage | 2 | M3.1–M3.3 |
| F6 adapter protocol + simulated agent | 2, 4 | M4.1–M4.2 |
| F7 guardrails | 2, 6 | M5.1–M5.3 |
| F8 runtime engine | 2, 3 | M6.1–M6.4 |
| F9 telemetry contract | 3, 4, 5 | M6.1, M8.2 |
| F10 CLI surface | all | M2.4, M8.1 |
| F11 packaged defaults | 1 | M2.3 |
| F12 documentation set | 1, 4 | M8.3 |
| F13 offline demos 01–03 | 4 | M9.1–M9.3 |
| F14 self-hosted CI | 3 | M0.4 |
| F15 GitHub Action | 1 | M10.1 |
| F16 queueing module | 3 | M7.1–M7.3 |
| F17 Monte-Carlo simulate | 1, 5 | M8.1 |
| F18 demos 04–05 | 3 | M9.4–M9.5 |
| F19 harness adapters | 4 | M4.3 |
| F20 GitLab/Jenkins how-tos | 1 | M8.3 (extends) |
| F21 recompute pipeline | 4, 5 | M8.2 |
| F22 property-based hardening | 2, 6 | M1.5, M5.1 (extend) |
| F23–F27 live-ops COULDs | 5 | v0.3 planning |
| F28 community harness adapters | 4 | post-M10 |
| F29 MCP governance server | 4 | post-M10 (requires F3, F16) |

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
| [spec/0008 CLI contract](../spec/0008-cli-contract.md) | F10 |
| [spec/0009 queueing](../spec/0009-queueing.md) | F16 |
| [spec/0010 triage](../spec/0010-triage.md) | F5 |
| [spec/0011 engine runtime](../spec/0011-engine-runtime.md) | F8 |
| [spec/0012 engineering baseline](../spec/0012-engineering-baseline.md) | F12, F14, quality attributes |
