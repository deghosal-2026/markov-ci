# markov-ci

**Markov-planned, guardrailed CI/CD — governance for agentic pipelines.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/markov-ci.svg)](https://pypi.org/project/markov-ci/)
[![Python 3.11 | 3.12 | 3.13](https://img.shields.io/pypi/pyversions/markov-ci.svg)](https://www.python.org/)
[![Status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)](CHANGELOG.md)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Types: mypy strict](https://img.shields.io/badge/types-mypy%20--strict-blue.svg)](https://mypy-lang.org/)
[![Docs: mkdocs](https://img.shields.io/badge/docs-mkdocs--material-526CFE.svg)](mkdocs.yml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

`markov-ci` models an agentic CI/CD pipeline as an **absorbing Markov chain** — a small
state space, measured transition probabilities, and three designed terminal outcomes —
instead of a deterministic DAG governed by brittle `if/else` retry rules. The chain is
the **planning** model (it forecasts cost and attempts and sizes the caps); at runtime a
bounded **governor** admits, checks and stops the repair loop — it does not sample the
chain. From the model `markov-ci` **forecasts** what your agents will cost, **governs**
them with hard limits at runtime, and **learns** from its own telemetry (ADR-0014).

> **Status: pre-1.0.** `v0.1.1` ("Trust") is the current release — the security and
> correctness fixes from the v0.1.1 review. **Upgrade from `v0.1.0`:** that release ran
> the harness prompt through a shell (a remote-code-execution path); `v0.1.1` makes
> harness invocation **argv-only** (ADR-0016). See the [CHANGELOG](CHANGELOG.md) and
> [SECURITY.md](SECURITY.md). The public API is not yet stable.

## The problem

CI/CD stopped being deterministic, for two reasons:

1. **Ephemeral infrastructure** — distributed suites, cloud runners, spot
   interruptions: identical commits now flake.
2. **AI agents in the loop** — agents triage, patch, and refactor inside pipelines,
   with probabilistic behavior (fix ~75% / loop ~15% / regress ~10% is a commonly
   cited ballpark, not a markov-ci measurement).

Governed by rigid rules, probabilistic agents give you one of two disasters: guardrails
so strict the agent never helps, or runaway retries that burn tokens, hang PRs, and
silently weaken your tests. And nobody can answer *"should the agent get 2 retries or
10?"* with a number.

## What it does

| | Capability | You get |
|---|---|---|
| 📊 | **Forecast** | Expected agent attempts, token spend, and outcome probabilities per failure category — before you enable anything. `N = (I−Q)⁻¹` · `B = N·R` · `t = N·1` · `C = N·c` |
| 🛡️ | **Govern** | Budget, attempt-cap, and confidence gates; enforced write allowlists; test-weakening hard-stopped; patches isolated to `ai-fix/*` branches; **humans always merge** |
| 🔁 | **Learn** | One versioned JSONL event per state hop; the transition matrix recomputes from your own telemetry, per failure category *and per agent harness* |

**Why it cannot run away:** attempt caps remove loop-back edges at assembly time, so
every chain markov-ci can execute is absorbing *by construction* — after the cap `Q` is
nilpotent, so absorption is a property of the **model**. The **runtime** stops via its
attempt counter plus per-call timeouts (a hung child is killed on timeout), so a run is
bounded even under adversarial probabilities.

> ⚠️ **Security notice (v0.1.1).** For `pull_request` events from **untrusted authors**
> (forks), enable container isolation (`container: python:3.12-slim`, or the
> `--container-image` flag) so PR code cannot reach host credentials; it is the
> recommended default for fork PRs. Without it, do **not** set `adapter: harness` on
> untrusted forks — use `adapter: simulated`. See [SECURITY.md](SECURITY.md) and
> [ADR-0013](docs/adr/0013-trust-boundary.md).

## Quick start

> The commands below are the v0.1.1 contract. Docs-are-tests: CI runs them verbatim
> (see `docs/quick-start.md`, executed by `tests/unit/docs/test_docs_are_tests.py`).
> **Install `v0.1.1` or later** — `v0.1.0` carries the harness shell-injection advisory
> (ADR-0016, [GHSA-5jj3-gcw8-pm5g](SECURITY.md)).

```bash
pip install -U "markov-ci>=0.1.1"        # PyPI; 3.11–3.13
# until 0.1.1 is on PyPI, install the release tag:
# pip install "markov-ci @ git+https://github.com/deghosal-2026/markov-ci@v0.1.1"

markov-ci analyze                                   # zero-config: prints the worked example
markov-ci analyze --category unit_assertion         # per-attempt decay + expected cost

# the offline demos live in the repo:
git clone https://github.com/deghosal-2026/markov-ci && cd markov-ci
markov-ci run examples/01-lint-error/config.yaml \
    --junit examples/01-lint-error/report.xml \
    --repo examples/01-lint-error/repo --seed 42
```

`markov-ci` is published on PyPI as [`markov-ci`](https://pypi.org/project/markov-ci/)
(Trusted Publishing, PEP 740 build provenance). No API keys, no network — the default
agent is a seeded, offline simulator. See the [quick start](docs/quick-start.md) for
the full five-minute path.

## How it works

A pipeline becomes a chain of decision states with three absorbing outcomes:

```
s0 verify ─▶ s1 triage ─▶ s2 agent ─▶ s3 worktree validation ─▶ s4 regression ─▶ a1 ready-for-review
                              ▲             │                              ▲
                              └──── loop ────┘        escalate ─▶ a2 · budget ─▶ a3
                         (attempt index in the state: s2#1, s3#2, …)
```

Per-attempt decay is modeled by **step-augmented states** (`s2#1`, `s2#2`, …), which
keeps the chain genuinely Markov so the closed-form math stays exact. The engine
evaluates gates strictly in order — **budget → attempt cap → confidence** — and every
hop emits a versioned telemetry event. Read
[the math, derived](docs/explanations/markov-model.md) or the
[architecture](docs/architecture.md).

## Documentation

Everything below also builds as a site — run `mkdocs serve`.

**Start here**

- [Overview — what & why](docs/OVERVIEW.md) — the concept in depth
- [Quick start](docs/quick-start.md) — first forecast in five minutes
- [Architecture](docs/architecture.md) — modules and data flow

**Guides**

- Tutorials: [01 — lint fix](docs/tutorials/01-lint-error-first-pass.md) · [02 — decay → escalate](docs/tutorials/02-assertion-decay-escalation.md) · [03 — infra timeout](docs/tutorials/03-infra-timeout-no-tokens.md) · [04 — runner pools](docs/tutorials/04-runner-pool-sizing.md) · [05 — GitHub Actions](docs/tutorials/05-github-actions-e2e.md) · [06 — adversarial runaway](docs/tutorials/06-adversarial-runaway.md) · [07 — cheating agent](docs/tutorials/07-cheating-agent.md)
- Examples: [01 lint error](examples/01-lint-error/README.md) · [02 assertion decay](examples/02-unit-assertion-decay/README.md) · [03 infra timeout](examples/03-infra-timeout/README.md) · [04 runner pools](examples/04-runner-pool-sizing/README.md) · [05 GitHub Actions (live)](examples/05-github-actions-e2e/README.md) · [06 adversarial runaway](examples/06-adversarial-runaway/README.md) · [07 cheating agent](examples/07-cheating-agent/README.md)
- How-to: [GitHub Actions](docs/how-to/integrate-github-actions.md) · [GitLab & Jenkins](docs/how-to/integrate-gitlab-jenkins.md) · [run the examples in Docker](docs/how-to/run-in-docker.md) · [use a local LLM](docs/how-to/use-a-local-llm.md)

**Reference & explanations**

- [Configuration](docs/reference/configuration.md) · [Telemetry](docs/reference/telemetry.md) · [CLI](docs/reference/cli.md)
- [The Markov model, derived](docs/explanations/markov-model.md) · [Queueing theory](docs/explanations/queueing-theory.md) · [Design review](docs/explanations/design-review.md)

**How this project is specified**

- [PRD](docs/prd/README.md) · [spec contracts](docs/spec/README.md) · [ADRs](docs/adr/README.md) · [WBS & issues](docs/WBS.md)

**Project files**

- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Code of Conduct](CODE_OF_CONDUCT.md) · [Changelog](CHANGELOG.md) · [License](LICENSE)

## Roadmap

| Release | Theme | Highlights |
|---|---|---|
| **v0.1.0** | *Absorption* | Shipped: math core · policy engine · triage · simulated, harness and local-LLM agents · guardrails · runtime · telemetry + `recompute` · queueing (Erlang-C + DES) · CLI (`validate`/`analyze`/`run`/`simulate`/`queue`/`recompute`) · composite GitHub Action · offline demos 01–07 |
| **v0.1.1** | *Trust* | **Shipped** ([PyPI](https://pypi.org/project/markov-ci/)): argv-only harness (ADR-0016) · diff-derived guardrails · worktree validation + opt-in container isolation · hard budgets (remaining-timeout → `a3`) · patch delivery (`--output-patch`, `--publish`) · model/runtime honesty (`analyze` from `s1`) · hardened test suite · field-test evidence |
| **v0.2.0** | *Capacity & reach* | Live harness verification (Claude Code / OpenCode / Aider) · MCP tool surface · drift/windowing |
| **v0.3.0** | *Live operations* | MCP governance server · currency cost model · drift alerts · community harness templates |

Full ticket-level breakdown: [v0.1.1 WBS](docs/WBS-v0.1.1.md) · [v0.1.0 WBS](docs/WBS.md).

## What it is not

Not an agent harness (it governs harnesses) · not auto-merge (`a1` is always a human
decision) · not a CI replacement (it plugs into GitHub Actions / GitLab / Jenkins) ·
not a dashboard (CLI + JSON events) · no telemetry leaves your machine.

## Contributing

Contributions are welcome once the repository goes public. Start with
[CONTRIBUTING.md](CONTRIBUTING.md) and the [ADRs](docs/adr/README.md) — every design
decision and its rationale is recorded there.

## License

[Apache-2.0](LICENSE).
