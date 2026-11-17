# ADR-0006: src/ layout, `py.typed`, `mypy --strict` from day one

**Status:** Accepted
**Date:** 2026-11-16

## Context

markov-ci runs *inside* CI runners, where a subtle import bug (tests importing the repo
instead of the installed package) can produce a green lie. The library's whole value is
being trustworthy math; the package must be verifiable by consumers' type checkers.

## Decision

src layout (`src/markov_ci/`), `py.typed` shipped in the wheel, `mypy --strict` and
`ruff` green at every milestone gate — not aspirational, enforced in CI.

## Consequences

- Import-safety: the installed package is what gets tested.
- Consumers get full typing — the API becomes checkable, not just readable.
- Some upfront annotation cost on every module; accepted.
- Falsifier: any `# type: ignore` requires a one-line justification comment; tracked
  to zero.
