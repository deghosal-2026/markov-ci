# Contributing to markov-ci

Thanks for your interest. markov-ci is **pre-alpha and private** during initial
development; contributions open up when the repository goes public at the v0.1.0
release gate. This guide is the contract contributors will be held to — written now so
the project is ready the day it flips public.

## Before you start

1. Read [docs/OVERVIEW.md](docs/OVERVIEW.md) — what markov-ci is and is not.
2. Read the [ADRs](docs/adr/README.md) — every architectural decision and its rationale
   is recorded there. If you want to change a decision, supersede an ADR; don't argue
   against code in a PR.
3. Read the [spec contracts](docs/spec/README.md) — the technical contracts the
   implementation must satisfy. **Contracts change via PR; supersede, don't silently
   rewrite.**

## Development workflow

```bash
git clone https://github.com/deghosal-2026/markov-ci && cd markov-ci
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Then, in the project's standing order:

1. **Write the test first** for the change — run it, confirm it fails (**RED**).
2. **Write the code** — run that test, confirm it passes (**GREEN**).
3. Run only the tests relevant to your change; the full suite + `ruff` + `mypy --strict`
   run once at the milestone gate.
4. Commit, push, open a PR.

## Quality bar (enforced, not aspirational)

| Check | Requirement |
|---|---|
| Types | `mypy --strict` clean; `# type: ignore` needs a justification comment |
| Lint/format | `ruff` clean |
| Tests | unit + integration for behavior changes; property tests for the math. **No skipped tests** — a guard is written (RED) with the artifact it protects, never `pytest.skip` |
| Docs | update the matching `docs/spec/` contract or reference page — **docs are tests** |
| Telemetry | never emit secrets; keep the [event contract](docs/reference/telemetry.md) |

`make test lint typecheck` runs the local gate.

## Project principles (they outrank features)

See [docs/prd/00-principles.md](docs/prd/00-principles.md). The short version: keep the
model Markov-correct by construction, keep absorption guaranteed, keep guardrails in
code (not comments), keep it offline-first, and never let anything auto-merge.

## Pull requests

- One focused change per PR; reference the WBS ticket (`M<N>.<T>`) and the spec contract
  or ADR it implements.
- Describe the behavior change and the test that proves it.
- Expect review against the principles and the spec — not against preference.

## Reporting bugs and proposing features

Use the issue templates (bug / feature / harness-adapter request) once published. For
security issues, see [SECURITY.md](SECURITY.md) — do **not** open a public issue.

## License

By contributing, you agree your contributions are licensed under
[Apache-2.0](LICENSE), per section 5 of the license.
