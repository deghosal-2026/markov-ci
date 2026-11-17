# WBS — markov-ci work breakdown

**Conventions (per team working rules):** one ticket at a time; test first (RED → GREEN);
run only the ticket's tests; each ticket ends implemented → tested → committed → pushed.
Ticket IDs are referenced in commits as `M<N>.<T>`.

**No skipped tests.** A test is either passing or failing — never skipped or conditionally
disabled. An enforcement test is written (RED) *with the artifact it guards*, never left as
a placeholder that skips until the artifact lands.

**Milestone gate (mandatory — every milestone M0–M11).** A milestone is **not complete**
until, on the merged milestone HEAD:

1. the **full test suite** passes (`make test`);
2. **≥ 95% line coverage** of `src/markov_ci` passes (`make cov`, enforced via
   `--cov-fail-under=95`);
3. **`ruff` is clean** (`make lint`);
4. **`mypy --strict` is clean** (`make typecheck`).

`make gate` runs 2–4 together. Half-done is not done: a coverage dip below 95%, a ruff
finding, or a mypy error **blocks the milestone** — it is fixed before the milestone's
tracking issues are closed. No milestone closes with a red gate.

**Tracking:** every ticket below is a GitHub issue ([repo issues](https://github.com/deghosal-2026/markov-ci/issues));
each milestone maps to a GitHub milestone. The `#` column is the issue number.

---

## M0 — Scaffold · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/1)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M0.1 | [#1](https://github.com/deghosal-2026/markov-ci/issues/1) | Repo skeleton | Tree per docs/architecture.md; `src/markov_ci/__init__.py`, `py.typed`; empty module dirs |
| M0.2 | [#2](https://github.com/deghosal-2026/markov-ci/issues/2) | `pyproject.toml` | hatchling src-layout; deps per spec/0012-engineering-baseline.md; ruff+mypy(strict)+pytest config |
| M0.3 | [#3](https://github.com/deghosal-2026/markov-ci/issues/3) | Makefile | `make test lint typecheck cov docs build` — each wired to a real tool |
| M0.4 | [#4](https://github.com/deghosal-2026/markov-ci/issues/4) | CI workflows | `ci.yml` (lint+typecheck+unit on PR), `integration.yml`, `cancel-closed-pr.yml` |
| M0.5 | [#5](https://github.com/deghosal-2026/markov-ci/issues/5) | Community health files | CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CHANGELOG (Keep a Changelog) |
| M0.6 | [#6](https://github.com/deghosal-2026/markov-ci/issues/6) | mkdocs site | `mkdocs.yml` + docs build green in CI (`docs.yml`) |

**Gate:** full suite + `ruff` + `mypy --strict` clean + **≥95% coverage** of
`src/markov_ci` on the empty-but-wired scaffold.

## M1 — Math core (`markov_ci.model`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/2)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M1.1 | [#7](https://github.com/deghosal-2026/markov-ci/issues/7) | State space types | `State`, `StateSpace`, absorbing/transient classification; unit tests |
| M1.2 | [#8](https://github.com/deghosal-2026/markov-ci/issues/8) | Step augmentation | base→`#attempt` expansion; loop-back edge generation; unit tests |
| M1.3 | [#9](https://github.com/deghosal-2026/markov-ci/issues/9) | Config→matrix assembly | `assemble()` per spec/0002-matrix-assembly.md incl. caps renormalization; unit tests |
| M1.4 | [#10](https://github.com/deghosal-2026/markov-ci/issues/10) | Matrix validation | row sums, reachability, absorbing identity; `validate` exit-code behaviour |
| M1.5 | [#11](https://github.com/deghosal-2026/markov-ci/issues/11) | Fundamental-matrix ops | `split`, `fundamental`, `absorption`, `steps_to_absorb`, `expected_cost`; property tests |
| M1.6 | [#12](https://github.com/deghosal-2026/markov-ci/issues/12) | Posteriors / CI | Dirichlet posterior + credible intervals from counts; property tests |
| M1.7 | [#13](https://github.com/deghosal-2026/markov-ci/issues/13) | Worked-example fixture | default config yields documented numbers (P(a1\|s0) ≈ 0.92); golden test |
| M1.8 | [#14](https://github.com/deghosal-2026/markov-ci/issues/14) | Property-based harness (F22) | hypothesis suite over matrix ops; adversarial `success=[1,1,1]` still absorbs |

**Gate:** milestone suite + `analyze` golden numbers (0.72 / 0.92) · **≥95% coverage** ·
`ruff` + `mypy --strict` clean.

## M2 — Policy + config (`markov_ci.policy`, `markov_ci.config`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/3)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M2.1 | [#15](https://github.com/deghosal-2026/markov-ci/issues/15) | Policy dataclass + gate order | budgets → cap → confidence; unit tests incl. a3 on budget trip |
| M2.2 | [#16](https://github.com/deghosal-2026/markov-ci/issues/16) | YAML loader (pydantic) | spec/0003 schema, unknown-key rejection, helpful errors; unit tests |
| M2.3 | [#17](https://github.com/deghosal-2026/markov-ci/issues/17) | Packaged default config | `markov_ci.data.default` = spec/0001-state-model.md defaults; loads+validates |
| M2.4 | [#18](https://github.com/deghosal-2026/markov-ci/issues/18) | `validate` + `analyze` CLI | exit codes 0/4; JSON output flag |

**Gate:** `validate`/`analyze` exit codes (0/4) green; zero-config `analyze` prints the
worked example · **≥95% coverage** · `ruff` + `mypy --strict` clean.

## M3 — Triage (`markov_ci.triage`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/4)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M3.1 | [#19](https://github.com/deghosal-2026/markov-ci/issues/19) | JUnit XML parser | failures → (name, message, type); robust fallback; fixture tests |
| M3.2 | [#20](https://github.com/deghosal-2026/markov-ci/issues/20) | Category classifier | spec/0010-triage.md categories; infra/dependency → a2 routing; fixture tests |
| M3.3 | [#21](https://github.com/deghosal-2026/markov-ci/issues/21) | Log minimizer | failing block + stack trace, 200-line cap; property tests |

**Gate:** every taxonomy fixture routed correctly; `infra_timeout`/`dependency_error` →
`a2` with **zero tokens** · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M4 — Agents (`markov_ci.agents`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/5)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M4.1 | [#22](https://github.com/deghosal-2026/markov-ci/issues/22) | Adapter protocol + types | `AgentAdapter`, `RepairContext`, `PatchProposal`; protocol conformance tests |
| M4.2 | [#23](https://github.com/deghosal-2026/markov-ci/issues/23) | SimulatedAgent | seeded, fixture-driven, calibrated to priors; determinism + fit tests |
| M4.3 | [#24](https://github.com/deghosal-2026/markov-ci/issues/24) | Harness adapter interface | headless CLI invocation per spec/0006; offline contract tests |
| M4.4 | [#25](https://github.com/deghosal-2026/markov-ci/issues/25) | Harness templates T2/T3 + conformance | claude/opencode/aider templates + BYO command; one conformance suite |

**Gate:** simulated agent deterministic (same seed → identical) and χ²-calibrated;
protocol conformance suite green · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M5 — Guardrails (`markov_ci.guardrails`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/6)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M5.1 | [#26](https://github.com/deghosal-2026/markov-ci/issues/26) | Path allowlist enforcement | allow/deny incl. always-denied set; adversarial cases (`.github`, `**/secrets/**`) |
| M5.2 | [#27](https://github.com/deghosal-2026/markov-ci/issues/27) | TMR checker | test-vs-src line ratio; assertion-deletion detection → hard stop |
| M5.3 | [#28](https://github.com/deghosal-2026/markov-ci/issues/28) | Branch manager | `ai-fix/pr-<n>` isolation; **no force-push code path exists**; tests assert absence |

**Gate:** all adversarial guardrail fixtures blocked (path traversal, symlink, assertion
deletion); absence-of-force-push asserted · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M6 — Engine (`markov_ci.engine`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/7)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M6.1 | [#29](https://github.com/deghosal-2026/markov-ci/issues/29) | RunResult + event emission | telemetry contract fields; crash-safe JSONL |
| M6.2 | [#30](https://github.com/deghosal-2026/markov-ci/issues/30) | Transition loop | spec/0011-engine-runtime.md algorithm; unit tests per hop decision |
| M6.3 | [#31](https://github.com/deghosal-2026/markov-ci/issues/31) | Sandbox apply-and-test | isolated worktree, run failing tests, revert; integration tests |
| M6.4 | [#32](https://github.com/deghosal-2026/markov-ci/issues/32) | `run` CLI | exit codes 0/2/3/4; `--seed`; end-to-end on fixtures |
| M6.5 | [#33](https://github.com/deghosal-2026/markov-ci/issues/33) | Telemetry JSON Schema artifact | `schemas/transition-event.schema.json`; reference page generated from it |

**Gate:** e2e fixtures reach their expected absorbing states; kill-mid-run leaves a valid
event stream · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M7 — Queueing (`markov_ci.queueing`) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/8)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M7.1 | [#34](https://github.com/deghosal-2026/markov-ci/issues/34) | Erlang-C | ρ, P_wait, Wq, p95; property tests vs closed-form; λ ≥ cμ rejected |
| M7.2 | [#35](https://github.com/deghosal-2026/markov-ci/issues/35) | DES simulator | bursty arrival patterns; convergence test vs Erlang-C under Poisson |
| M7.3 | [#36](https://github.com/deghosal-2026/markov-ci/issues/36) | `queue` CLI | `--lambda/--mu/--c`, `--simulate`, JSON output |

**Gate:** Erlang-C matches closed-form references; DES converges to Erlang-C under Poisson
· ≥95% coverage · `ruff` + `mypy --strict` clean.

## M8 — CLI polish + docs build · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/9)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M8.1 | [#37](https://github.com/deghosal-2026/markov-ci/issues/37) | `simulate` command | Monte-Carlo absorption stats vs analytic B (within CI) |
| M8.2 | [#38](https://github.com/deghosal-2026/markov-ci/issues/38) | `recompute` command | events.jsonl → empirical matrix; round-trip golden test |
| M8.3 | [#39](https://github.com/deghosal-2026/markov-ci/issues/39) | Docs site complete | every reference page matches shipped code; `make docs` green; docs-are-tests |
| M8.4 | [#40](https://github.com/deghosal-2026/markov-ci/issues/40) | GitLab/Jenkins docs (F20) | integration how-tos + CI examples; exit-code contract shown |

**Gate:** quick-start commands execute in CI (docs-are-tests); `recompute` round-trip
golden test green · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M9 — Examples (demos) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/10)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M9.1 | [#41](https://github.com/deghosal-2026/markov-ci/issues/41) | `01-lint-error` | first-pass green; deterministic seed; tutorial matches output |
| M9.2 | [#42](https://github.com/deghosal-2026/markov-ci/issues/42) | `02-unit-assertion-decay` | decay → a2; expected-token math shown |
| M9.3 | [#43](https://github.com/deghosal-2026/markov-ci/issues/43) | `03-infra-timeout` | zero tokens, immediate a2 |
| M9.4 | [#44](https://github.com/deghosal-2026/markov-ci/issues/44) | `04-runner-pool-sizing` | Erlang-C + burst simulation report |
| M9.5 | [#45](https://github.com/deghosal-2026/markov-ci/issues/45) | `05-github-actions-e2e` (live) | workflow runs on a real PR (opt-in secrets); depends on M10.1 |
| M9.6 | [#61](https://github.com/deghosal-2026/markov-ci/issues/61) | Docker runner for the offline examples | pinned-python image + git; compose runs demos 01–04 under `--network none`; image scanned by [#60](https://github.com/deghosal-2026/markov-ci/issues/60) |

**Convention:** every `examples/<NN>-<name>/` directory ships its own `README.md` (how to
run it, the expected exit code, the expected event stream) and is covered by a tutorial in
`docs/tutorials/`. The example READMEs and the tutorials are both linked from the root
`README.md`. **The enforcing test is written (RED) in M9.1** as part of that ticket — there
are no placeholder or skipped tests: an enforcement test is created with the artifact it
guards.

**Gate:** demos 01–04 byte-stable under `--seed` and match their tutorials; every example
has a README; the Docker runner (#61) reproduces them under `--network none` ·
≥95% coverage · `ruff` + `mypy --strict` clean.

## M10 — Releases and articles · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/11)

*Staging:* v0.1.0 = F1–F14 + public flip + articles 1–2 · v0.2.0 = GitHub Action + article 3 · v0.3.0 = article 4.

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M10.1 | [#46](https://github.com/deghosal-2026/markov-ci/issues/46) | Root `action.yml` (F15) | composite action wrapping CLI; tested on a test repo PR |
| M10.2 | [#47](https://github.com/deghosal-2026/markov-ci/issues/47) | Release readiness (v0.1.0) | CHANGELOG, version 0.1.0, tag, GitHub Release, PyPI publish via **Trusted Publishing** (name check first); gated by **M10.8** |
| M10.3 | [#48](https://github.com/deghosal-2026/markov-ci/issues/48) | Public flip | `gh repo edit --visibility public` + README badges + topics |
| M10.4 | [#49](https://github.com/deghosal-2026/markov-ci/issues/49) | Article 1 | Dev.To + LinkedIn: DAG → Markov concept piece |
| M10.5 | [#50](https://github.com/deghosal-2026/markov-ci/issues/50) | Article 2 | Build log + "what the original article got wrong" |
| M10.6 | [#51](https://github.com/deghosal-2026/markov-ci/issues/51) | Article 3 | Queueing theory for runner fleets (+ harness cost hook) |
| M10.7 | [#52](https://github.com/deghosal-2026/markov-ci/issues/52) | Article 4 | Measuring agentic CI (metrics + anti-patterns) |
| M10.8 | [#60](https://github.com/deghosal-2026/markov-ci/issues/60) | Release security & supply-chain gate | trufflehog/gitleaks **history** scan · `pip-audit` · `bandit` · SBOM + PyPI attestations; **blocking** before publish |

**Gate:** v0.1.0 installs from PyPI and runs `analyze`; the composite Action is tested on a
PR; **M10.8 security gate is green** (clean history secret scan, no known-vulnerable deps,
no high-severity SAST) · ≥95% coverage · `ruff` + `mypy --strict` clean.

## M11 — Live operations (v0.3) · [milestone](https://github.com/deghosal-2026/markov-ci/milestone/12)

| ID | # | Ticket | Deliverable / acceptance |
|---|---|---|---|
| M11.1 | [#53](https://github.com/deghosal-2026/markov-ci/issues/53) | Cost model in currency (F23) | per-state `$` cost vectors; org price cards |
| M11.2 | [#54](https://github.com/deghosal-2026/markov-ci/issues/54) | A/B policy comparison (F24) | two configs side-by-side: outcome/cost deltas |
| M11.3 | [#55](https://github.com/deghosal-2026/markov-ci/issues/55) | State-space visualization (F25) | Mermaid graph + N-heatmap export |
| M11.4 | [#56](https://github.com/deghosal-2026/markov-ci/issues/56) | Multi-pipeline aggregation (F26) | org-level matrix across repos |
| M11.5 | [#57](https://github.com/deghosal-2026/markov-ci/issues/57) | Time-varying matrices / drift (F27) | weekly recompute recipes; drift alerts beyond CI |
| M11.6 | [#58](https://github.com/deghosal-2026/markov-ci/issues/58) | Community harness templates (F28) | more verified headless templates via the shared protocol |
| M11.7 | [#59](https://github.com/deghosal-2026/markov-ci/issues/59) | MCP governance server (F29) | expose `analyze`/`validate`/`queue` as MCP tools |

---

**Gate:** v0.3 live-ops features green; no regression against the NSM metric baseline ·
≥95% coverage · `ruff` + `mypy --strict` clean.

---

**Dependency notes:** M1 → M2 → (M3 ∥ M4 ∥ M5) → M6 → (M7 ∥ M8) → M9 → M10 → M11.
Docs (`docs/`) are contract-first and already written; M8.3 trues them up to shipped code.
