# WBS — markov-ci work breakdown

**Conventions (per team working rules):** one ticket at a time; test first (RED → GREEN);
run only the ticket's tests; full suite + ruff + mypy --strict once per milestone gate;
each ticket ends implemented → tested → committed → pushed. Ticket IDs are referenced in
commits as `M<N>.<T>`.

---

## M0 — Scaffold

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M0.1 | Repo skeleton | Tree per docs/architecture.md; `src/markov_ci/__init__.py`, `py.typed`; empty module dirs |
| M0.2 | `pyproject.toml` | hatchling src-layout build; deps (spec/0012-engineering-baseline.md); ruff+mypy(strict)+pytest config |
| M0.3 | Makefile | `make test lint typecheck cov docs build` — each wired to real tool |
| M0.4 | CI workflows | `ci.yml` (lint+typecheck+unit on PR), `integration.yml`, `cancel-closed-pr.yml` |
| M0.5 | Community health files | CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, CHANGELOG.md (Keep a Changelog) |
| M0.6 | mkdocs site | `mkdocs.yml` + docs build green in CI (`docs.yml`) |

**Gate:** full suite + lint + typecheck green on empty-but-wired scaffold.

## M1 — Math core (`markov_ci.model`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M1.1 | State space types | `State`, `StateSpace`, absorbing/transient classification; unit tests |
| M1.2 | Step augmentation | base→`#attempt` expansion; loop-back edge generation; unit tests |
| M1.3 | Config→matrix assembly | `assemble()` per spec/0002-matrix-assembly.md incl. caps renormalization; unit tests |
| M1.4 | Validation | row sums, reachability, absorbing identity; `validate` exit-code behavior |
| M1.5 | Fundamental matrix ops | `split`, `fundamental`, `absorption`, `steps_to_absorb`, `expected_cost`; property tests (B rows sum 1, N ≥ 0) |
| M1.6 | Posteriors/CI | Dirichlet posterior + credible intervals from counts; property tests |
| M1.7 | Worked-example fixture | default config yields documented numbers (P(a1\|s0) ≈ 0.92); golden test |

**Gate:** milestone suite + `analyze` golden numbers.

## M2 — Policy + config (`markov_ci.policy`, `markov_ci.config`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M2.1 | Policy dataclass + evaluation order | budgets → cap → confidence; unit tests incl. a3 on budget trip |
| M2.2 | YAML loader (pydantic) | full schema, unknown-key rejection, helpful errors; unit tests |
| M2.3 | Packaged default config | `markov_ci.data.default` = SPEC §2 defaults; loads+validates |
| M2.4 | `validate` + `analyze` CLI | exit codes 0/4; JSON output flag |

## M3 — Triage (`markov_ci.triage`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M3.1 | JUnit XML parser | failures → (name, message, type); fixture tests |
| M3.2 | Category classifier | spec/0010-triage.md categories; infra/dependency → a2 routing; fixture tests |
| M3.3 | Log minimizer | failing block + stack trace, 200-line cap; property tests on line cap |

## M4 — Agents (`markov_ci.agents`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M4.1 | Adapter protocol + RepairContext/PatchProposal types | typing-only ticket; protocol conformance tests |
| M4.2 | SimulatedAgent | seeded, fixture-driven, calibrated to priors; determinism tests |
| M4.3 | Harness adapter interface (headless CLI) + tests | offline contract tests only (no network in CI) |

## M5 — Guardrails (`markov_ci.guardrails`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M5.1 | Path allowlist enforcement | allow/deny matching incl. always-denied set; adversarial cases (`.github`, `**/secrets/**`) |
| M5.2 | TMR checker | test-vs-src line ratio; assertion-deletion detection → hard stop |
| M5.3 | Branch manager | `ai-fix/pr-<n>` isolation; **no force-push code path exists**; tests assert absence |

## M6 — Engine (`markov_ci.engine`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M6.1 | RunResult + event emission | telemetry contract fields; crash-safe JSONL |
| M6.2 | Transition loop | spec/0011-engine-runtime.md algorithm; unit tests per hop decision |
| M6.3 | Sandbox apply-and-test | isolated worktree, run failing tests, revert; integration tests |
| M6.4 | `run` CLI | exit codes 0/2/3/4; `--seed`; end-to-end on fixtures |

## M7 — Queueing (`markov_ci.queueing`)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M7.1 | Erlang-C | ρ, P_wait, Wq, p95; property tests vs closed-form; lam ≥ cμ rejected |
| M7.2 | DES simulator | bursty arrival patterns; convergence test vs Erlang-C under Poisson |
| M7.3 | `queue` CLI | `--lambda/--mu/--c`, `--simulate`, JSON output |

## M8 — CLI polish + docs build

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M8.1 | `simulate` command | Monte-Carlo absorption stats vs analytic B (within CI) |
| M8.2 | `recompute` command | events.jsonl → empirical matrix; round-trip golden test |
| M8.3 | Docs site complete | every reference page matches shipped code; `make docs` green |

## M9 — Examples (offline)

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M9.1 | `01-lint-error` | first-pass green; deterministic seed; tutorial matches output |
| M9.2 | `02-unit-assertion-decay` | decay → a2; expected-token math shown |
| M9.3 | `03-infra-timeout` | zero tokens, immediate a2 |
| M9.4 | `04-runner-pool-sizing` | Erlang-C + burst simulation report |
| M9.5 | `05-github-actions-e2e` | workflow runs on this repo's own PRs (opt-in secrets) |

## M10 — Action + release + articles

| ID | Ticket | Deliverable / acceptance |
|---|---|---|
| M10.1 | Root `action.yml` | composite action wrapping CLI; tested on a test repo PR |
| M10.2 | Release readiness | CHANGELOG, version 0.1.0, tag, GitHub Release, PyPI publish (name check first) |
| M10.3 | Public flip | `gh repo edit --visibility public` + README badges + topics |
| M10.4 | Article 1 | Dev.To + LinkedIn: DAG → Markov concept piece |
| M10.5 | Article 2 | Build log + "what the original article got wrong" |
| M10.6 | Article 3 | Queueing theory for runner fleets |
| M10.7 | Article 4 | Measuring agentic CI (metrics + anti-patterns) |

---

**Dependency notes:** M1 → M2 → (M3 ∥ M4 ∥ M5) → M6 → (M7 ∥ M8) → M9 → M10.
Docs (`docs/`) are contract-first and already written; M8.3 trues them up to shipped code.
