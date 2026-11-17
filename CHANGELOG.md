# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Forecast** — `markov-ci analyze` prints the fundamental matrix `N`, absorption
  probabilities `B`, expected steps `t`, and expected cost `C`, with Dirichlet
  credible intervals from telemetry (`src/markov_ci/model/`, spec 0002).
- **Govern** — the governed runtime loop with strictly-ordered gates (budget → attempt
  cap → confidence), enforced write allowlists, the test-modification-ratio hard stop,
  `ai-fix/*` branch isolation, and no force-push or auto-merge code path
  (`engine/`, `policy/`, `guardrails/`; spec 0004/0005/0011).
- **Triage** — deterministic JUnit/log classification; infra and dependency failures
  escalate with zero tokens (`triage/`, spec 0010).
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
  (#61).
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

### Notes

- Pre-alpha; the public API is not yet stable. `v0.1.0` is the first tagged release
  (M10.2, #47); the CLI, config, and telemetry contracts in `docs/spec/` are what it
  satisfies. Field-test evidence for the shipped milestone runs lives under
  `field-test/`.

<!--
Release entries follow Keep a Changelog sections: Added, Changed, Deprecated,
Removed, Fixed, Security. The v0.1.0 entry is written in M10.2 (#47).
-->
