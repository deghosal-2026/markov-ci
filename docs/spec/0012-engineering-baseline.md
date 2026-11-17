# Spec 0012 — Engineering baseline

**Status:** Stable · **Implements:** PRD §11 (quality attributes)

## 1. Packaging & compatibility

- Python ≥ 3.11 (test 3.11/3.12/3.13); src layout `src/markov_ci/`; `py.typed`.
- Runtime deps: `numpy`, `pydantic ≥ 2`, `PyYAML`, `typer`, `rich`, `jsonschema`,
  `defusedxml` (hardened parsing of the runner-produced JUnit XML).
- **No runtime dependency on any LLM SDK or harness SDK in core** — harness adapters
  are extras (`markov-ci[harness]`).
- Dev extras: `pytest`, `hypothesis`, `ruff`, `mypy`, `mkdocs-material`.
- `mypy --strict` and `ruff` clean at every milestone gate — enforced, not aspirational.

## 2. Testing strategy

| Tier | What | Examples |
|---|---|---|
| `tests/unit` | per-module behavior + math properties | B rows sum to 1; N ≥ 0; t finite; C monotone in c; row-sum tolerance 1e-9; minimizer line cap |
| `tests/integration` | wiring: config → assembly → policy → engine | fixture JUnit files per category; adversarial guardrail fixtures |
| `tests/e2e` | the five demo scenarios offline | deterministic seeds; assert absorbing state, visits, event stream |
| property-based | `hypothesis` over matrix ops, triage parsing, path matching | absorption under adversarial priors (`success=[1,1,1]` still terminates) |

Golden fixtures: default config assembly + `P(a1|s2) ≈ 0.72`, `P(a1|s0) ≈ 0.92` — docs
and tutorials must not drift from these (docs-are-tests).

## 3. Versioning

- Semver for releases; `version` in config and `schema_version` in events bump on
  breaking change; `recompute` accepts all event versions ≤ current.
- `CHANGELOG.md` maintained from the first release (Keep a Changelog format).
- Contracts in `spec/` are amended via PR with an `Amends:` header — supersede, never
  silently rewrite.

## 4. CI (self-hosted, F14)

PRs run: ruff → mypy --strict → unit → integration → demos offline → mkdocs build.
The repo's own delivery is governed by markov-ci's gates from day one.
