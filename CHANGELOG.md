# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Documentation set: `docs/OVERVIEW.md`, the `docs/prd/` sub-PRDs (product
  requirements incl. Critical User Journeys and the harness-compatibility strategy),
  `docs/spec/` contracts, `docs/adr/` decision records, and `docs/WBS.md`.
- `README.md` with badges, `CONTRIBUTING.md`, `SECURITY.md` (incl. the release
  security & supply-chain gate), `CODE_OF_CONDUCT.md`.
- Packaging and toolchain: `pyproject.toml` (hatchling, ruff, `mypy --strict`,
  pytest), `Makefile`, CI workflows (`ci`, `integration`, `cancel-closed-pr`,
  `security`).
- `src/markov_ci/` package skeleton and `tests/` layout.

### Notes

- Pre-alpha. The public API is not yet stable; the CLI, config, and telemetry
  contracts described in `docs/spec/` are the contract v0.1.0 must satisfy.

<!--
Release entries follow Keep a Changelog sections: Added, Changed, Deprecated,
Removed, Fixed, Security. The v0.1.0 entry is written in M10.2 (#47).
-->
