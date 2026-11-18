# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-11-18

The **trust** release: the v0.1.1 review fixes (FIX-01 … FIX-05), the argv-only
harness, diff-derived guardrails, worktree validation with a real container option,
patch delivery, model/runtime honesty, and the test-suite hardening.

### Security

- **FIX-01 — shell injection (Critical).** The harness adapter is **argv-only**: the
  command template is split with `shlex.split` before `%PROMPT%` is substituted, the
  prompt becomes one argv element, and the process runs with `shell=False` (ADR-0016).
  The ad-hoc `"`-escaping and the `# nosec B602` suppression are gone. Templates are
  validated at config load; shell re-entry (`sh -c … %PROMPT%`) is rejected; the
  optional `%PROMPT_FILE%` keeps long prompts off `ps` / ARG_MAX.
- **FIX-02 — guardrails derive paths from the diff.** The allowlist checks
  **derived ∪ declared** paths, fails closed when a non-empty diff's paths cannot be
  determined, denies symlink creation, and re-runs on git's own
  `git diff --name-status -M` after apply. The always-denied set is hardened
  (`.env*`, CI + build configs, `CODEOWNERS`, credentials/keys) with case-insensitive
  gitignore semantics via `pathspec`.
- **FIX-04 — worktree validation and hard budgets.** Validation runs in a fresh clone
  (`--no-hardlinks --local`; no shared hooks/config/credentials), with an allowlisted
  environment (no `GITHUB_TOKEN` / `ACTIONS_*` / `*_TOKEN` / `*_KEY` / `*_SECRET`), a
  process-group kill on timeout, `resource` limits, and remaining-wall-clock timeouts.
  An opt-in **container** path (`--network=none`, read-only checkout, tmpfs work dir,
  non-root) is the recommended default for fork PRs. The word "sandbox" is retired
  (ADR-0012) — it is worktree validation.
- Release security & supply-chain gate (M13.32–M13.36): the release workflow now runs
  the **test suite** before building, pins every action by full commit SHA, uses PyPI
  **Trusted Publishing** (OIDC + PEP 740 attestations) with no long-lived token, and
  enforces **branch coverage ≥ 95%** in CI.

### Fixed

- `run` no longer discards a validated fix: `RunResult.patch` / `--output-patch` and an
  Action artifact persist it; `--publish` applies **only** the validated diff to a fresh
  `ai-fix/*` branch (paths-only, never force, reports the branch only after a push).
- Retries carry new information (the minimized, scrubbed validation output plus the
  previous diff); a validation/harness timeout absorbs in `a3` **with an event**; every
  exit path (ineligible triage, harness error, internal error) emits a terminal event
  and a documented exit code.
- `recompute` passes the config prior + `alpha`, excludes simulated events by default,
  and events carry `synthetic`, `gate_rejected`, `config_hash` and `model_version`.
- Config validation: prior `success` must lie in `[0, 1]`; every assembled matrix entry
  is checked; the config `version` is checked before the schema; the dead `cost_weight`
  key and the empty `[harness]` extra are removed.
- `analyze` defaults to the `s1` (failed-builds) start state and prints **both** the
  all-builds and failed-builds rows; `P(a3)` is labelled "not modelled — `simulate`
  only"; the confidence gate is modelled in assembly.

### Changed

- **Breaking:** the `run` exit-code contract changed (FIX-03, ADR-0017). `a2` now exits
  `1` (was `2`); `2` is reserved for Click usage errors. The full contract is
  `0` = `a1`, `1` = `a2`, `2` = usage error, `3` = `a3`, `4` = invalid input,
  `5` = internal failure. Spec 0008 and the CLI reference were updated. CI that branches
  on exit codes must be updated.
- The engine's validation step is **worktree validation**, not a "sandbox" (ADR-0012);
  the runtime is documented as a capped, guardrailed retry governor whose chain is a
  planning model (PRD-01).
- Token accounting reports `null` when a harness reports no usage — the token cap then
  does not bind (spec 0007).

## [0.1.0] - 2026-11-16

The first tagged release: **absorption** — the math core, the governed runtime,
the guardrails, the offline proof suite, and the composite GitHub Action.

### Added

- **Forecast** — `markov-ci analyze` prints the fundamental matrix `N`, absorption
  probabilities `B`, expected steps `t`, and expected cost `C`, with Dirichlet
  credible intervals from telemetry (`src/markov_ci/model/`, spec 0002).
- **Govern** — the governed runtime loop with strictly-ordered gates (budget → attempt
  cap → confidence), enforced write allowlists, the test-modification-ratio hard stop,
  `ai-fix/*` branch isolation, and no force-push or auto-merge code path
  (`engine/`, `policy/`, `guardrails/`; spec 0004/0005/0011).
- **Triage** — deterministic JUnit/log classification; infra and dependency failures
  escalate with zero tokens (`triage/`, spec 0010). JUnit parsing is hardened with
  `defusedxml`.
- **Agents** — the one-method adapter protocol, the seeded offline `SimulatedAgent`, and
  harness adapters for Claude Code / OpenCode / Aider, plus a stdlib-only
  OpenAI-compatible local-LLM adapter (`agents/`; spec 0006, ADR-0003/0007/0011).
- **Queueing** — Erlang-C runner-pool sizing and a discrete-event simulator for bursty
  agent traffic (`queueing/`, spec 0009).
- **Telemetry** — versioned JSONL transition events (JSON-Schema-checked) and
  `markov-ci recompute` from events to empirical priors per *(category × adapter)*
  (`telemetry/`, spec 0007).
- CLI: `validate`, `analyze`, `run`, `simulate`, `queue`, `recompute` with the stable
  exit-code contract (`0/2/3/4`, spec 0008). `run` accepts `--repo`, `--adapter`,
  `--max-tokens`, and `--wall-clock` overrides.
- The offline proof-suite demos (`examples/01-…` through `07-…`) and the Docker runner
  (#61): demos 01–04 run under `docker compose` with `--network none`, asserting their
  documented exit codes.
- The root composite **GitHub Action** (`action.yml`) wrapping the CLI, verified on a
  live GitHub runner (`.github/workflows/markov-ci-e2e.yml`).
- Documentation set: `docs/OVERVIEW.md`, the `docs/prd/` sub-PRDs (incl. Critical User
  Journeys and the harness-compatibility strategy), `docs/spec/` contracts,
  `docs/adr/`, `docs/WBS.md`, the tutorials, and the reference pages.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md` (incl. the release security &
  supply-chain gate), `CODE_OF_CONDUCT.md`.
- Packaging and toolchain: `pyproject.toml` (hatchling, ruff, `mypy --strict`,
  pytest), `Makefile`, CI workflows (`ci`, `integration`, `docs`, `security`,
  `cancel-closed-pr`, `markov-ci-e2e`).

### Security

- Release gate (M10.8, #60): full-history secret scan (gitleaks + trufflehog),
  `pip-audit`, `bandit` (0 medium/high findings), license check, and SBOM
  generation — all green on the release commit, and re-run as a blocking stage of
  the release workflow itself. v0.1.0 publishes via a scoped PyPI API token held
  only as an encrypted GitHub Actions secret; Trusted Publishing (OIDC + PEP 740
  attestations) is the follow-up.

<!--
Release entries follow Keep a Changelog sections: Added, Changed, Deprecated,
Removed, Fixed, Security. The v0.1.0 entry is written in M10.2 (#47).
-->
