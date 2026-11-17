# 06 — Features: MUST have (v0.1.0 — "the promise")

Priorities: **MUST** = v0.1.0 blocker. **SHOULD** = v0.2.0. **COULD** = v0.3+.
**WON'T** = explicitly rejected for v0.x. IDs are stable, referenced by WBS tickets,
spec contracts, and the CUJ traceability matrix (appendix 13).

**The MUST list at a glance** — v0.1.0 does not ship without all fourteen:

| # | Feature | One-line essence | CUJ |
|---|---|---|---|
| F1 | State-space configuration | YAML states/transitions/priors; step augmentation | CUJ-1 |
| F2 | Matrix assembly + validation | Canonical Q/R; caps ⇒ absorption; strict validation | CUJ-1, CUJ-3 |
| F3 | Forecast math | `N`, `B`, `t`, `C` + Dirichlet CIs — the answer to "2 retries or 10?" | CUJ-1, CUJ-5 |
| F4 | Policy engine | Budget → cap → confidence gates, strictly ordered | CUJ-1, CUJ-3 |
| F5 | Deterministic triage | JUnit/log → category; infra flakes never reach an agent | CUJ-2 |
| F6 | Adapter protocol + simulated agent | One-method protocol; offline, seeded, calibrated | CUJ-2, CUJ-4 |
| F7 | Enforced guardrails | Allowlist, TMR, branch isolation, no force-push, no auto-merge | CUJ-2, CUJ-6 |
| F8 | Runtime engine | The governed loop + sandbox + RunResult | CUJ-2, CUJ-3 |
| F9 | Telemetry contract | Versioned JSONL; events alone recompute the matrix | CUJ-3, CUJ-4, CUJ-5 |
| F10 | CLI surface | validate/analyze/run + stable exit-code contract | all |
| F11 | Packaged defaults | Zero-config `analyze` works out of the box | CUJ-1 |
| F12 | Documentation set | Quick-start through math derivations; docs-are-tests | CUJ-1, CUJ-4 |
| F13 | Offline demos 01–03 | First-pass green · decay→escalate · zero-token infra | CUJ-4 |
| F14 | Self-hosted CI | This repo's own PRs run markov-ci's gates | CUJ-3 |

---

**F1 — State-space configuration (YAML).** Declare states (transient/absorbing),
transitions with probabilities, per-category priors, and policy in one validated file.
Step augmentation (`s2#1`, `s3#2`, …) generated from `max_attempts`.
*AC:* default config loads+validates; unknown keys rejected with line numbers; invalid
row sum → exit 4 with actionable message.

**F2 — Matrix assembly + validation.** Canonical `P = [[Q, R], [0, I]]`; cap-driven
renormalization at `max_attempts` (this is the absorption guarantee); row sums (±1e-9);
transient→absorbing reachability check.
*AC:* `validate` exits 4 on: bad row sum, unreachable absorption, non-identity absorbing
row, unknown state reference. Golden assembly test on default config.

**F3 — Forecast math engine.** `N = (I−Q)⁻¹`, `B = N·R`, `t = N·1`, `C = N·c`
(user-supplied per-state cost vector), Dirichlet posterior CIs from counts.
*AC:* property tests (B rows sum to 1; N ≥ 0; t finite; C monotone in c); golden numbers
on default config (P(a1|s2) ≈ 0.72, P(a1|s0) ≈ 0.92).

**F4 — Policy engine.** Ordered gate: budget → attempt cap → confidence threshold →
transition. Fields: `min_confidence` (0.40), `max_attempts` (3), `max_tokens` (200k),
`wall_clock_seconds` (900). Every rejection lands in a designed absorbing state.
*AC:* unit test per gate order; budget trip → `a3` even mid-attempt.

**F5 — Deterministic failure triage.** JUnit XML + log input → category in
{lint_error, type_mismatch, unit_assertion, infra_timeout, dependency_error, unknown} +
minimized context (failing block + stack trace, ≤ 200 lines). Routing: infra/dependency
→ `a2` immediately.
*AC:* fixture suite (one per category, incl. timeout + connection-refused patterns);
minimizer never exceeds cap (property test); `unknown` → `a2` unless opted in.

**F6 — Agent adapter protocol + simulated agent.** One-method protocol
(`repair(ctx) -> PatchProposal`); `SimulatedAgent` seeded, fixture-driven, calibrated so
observed outcomes match priors statistically.
*AC:* same seed → byte-identical run; χ² goodness-of-fit vs prior (seeded tolerance);
protocol conformance suite passes for simulated agent.

**F7 — Enforced guardrails.** (a) Path allowlist: default write = `src/**`, `tests/**`;
always-denied regardless of config: `.github/**`, `.git`, secrets (`*.env`,
`**/secrets/**`), CI configs, lockfiles, LICENSE. (b) TMR checker: test-lines/src-lines
ratio > 1.0 or any assertion deletion → hard stop + mandatory-review flag. (c) Branch
isolation: `ai-fix/pr-<n>` / `ai-fix/local-<run_id>`; **no force-push code path exists**.
(d) No auto-merge: `a1` posts a review summary; merging is human-only.
*AC:* adversarial fixture suite (path traversal, symlink, renamed test, deleted
assertion) all blocked; absence-of-force-push asserted by test.

**F8 — Runtime engine.** Governed loop (spec 0011): triage → assemble → hop; sandbox
apply-and-test in an isolated worktree; crash-safe JSONL event per hop; `RunResult` =
absorbing state + visit counts + tokens + wall-clock + guardrail report.
*AC:* e2e fixtures → expected absorbing states; kill-mid-run leaves valid partial event
stream.

**F9 — Telemetry contract.** Versioned JSONL events (`schema_version`, `run_id`,
`commit_sha`, `pr_number`, `from_state`, `to_state`, `duration_ms`, `tokens_used`,
`failure_category`, `attempt`, `adapter`, `ts`). Events alone are sufficient to recompute
the matrix — per failure category and per adapter.
*AC:* JSON Schema in `schemas/` validates every emitted event; no secret ever in events;
`adapter` present on every event so per-harness matrices fall out of `recompute`.

**F10 — CLI surface.** `validate`, `analyze`, `run` + exit-code contract:
0 = a1, 2 = a2, 3 = a3, 4 = invalid config. Global: `--config` (default: packaged),
`--seed`, `--json`.
*AC:* exit-code contract test; `--json` output stable enough for CI assertions.

**F11 — Packaged defaults.** The literature-derived default state space + priors ship in
the wheel; zero-config `analyze` works out of the box.
*AC:* `markov-ci analyze` with no args prints the worked example.

**F12 — Documentation set.** Quick-start (5 min, no API key), math derivation
(explanations/markov-model.md), config/telemetry/CLI reference, tutorials for demos 01–03,
ADRs for the core decisions; mkdocs site builds in CI.
*AC:* every code block in quick-start executed verbatim in CI (docs-are-tests).

**F13 — Offline demos 01–03.** `01-lint-error` (first-pass green), `02-unit-assertion-decay`
(decay → a2 with the math shown), `03-infra-timeout` (zero tokens, immediate a2).
*AC:* each runs in CI with no network; outputs byte-stable under `--seed`; tutorials
match actual output.

**F14 — Self-hosted CI.** This repo's own PRs run markov-ci's gates (lint, typecheck,
unit, integration, demos) — the product governs its own delivery from day one.
*AC:* PR workflow green; demo scenarios are CI jobs.
