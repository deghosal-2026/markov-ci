# markov-ci

**Markov-governed, self-healing CI/CD — governance for agentic pipelines.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11 | 3.12 | 3.13](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Status: pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)](docs/WBS.md)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Types: mypy strict](https://img.shields.io/badge/types-mypy%20--strict-blue.svg)](https://mypy-lang.org/)
[![Docs: mkdocs](https://img.shields.io/badge/docs-mkdocs--material-526CFE.svg)](mkdocs.yml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

`markov-ci` models an agentic CI/CD pipeline as an **absorbing Markov chain** — a small
state space, measured transition probabilities, and three designed terminal outcomes —
instead of a deterministic DAG governed by brittle `if/else` retry rules. From that
model it **forecasts** what your agents will cost, **governs** them with hard limits at
runtime, and **learns** from its own telemetry.

> **Status: pre-alpha.** Private during initial development; intended for open-source
> release under Apache-2.0. The CLI, config, and telemetry contracts are specified and
> documented; implementation lands per the [WBS](docs/WBS.md).

## The problem

CI/CD stopped being deterministic, for two reasons:

1. **Ephemeral infrastructure** — distributed suites, cloud runners, spot
   interruptions: identical commits now flake.
2. **AI agents in the loop** — agents triage, patch, and refactor inside pipelines,
   with probabilistic behavior (fix ~75% / loop ~15% / regress ~10% is typical).

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
every chain markov-ci can execute is absorbing *by construction*. Termination is a
theorem, not a timeout — even under adversarial probabilities.

## Quick start

> The commands below are the v0.1.0 contract. Docs-are-tests: CI will run them verbatim
> once the CLI lands.

```bash
git clone https://github.com/deghosal-2026/markov-ci && cd markov-ci
pip install -e ".[dev]"

markov-ci analyze                                   # zero-config: prints the worked example
markov-ci analyze --category unit_assertion         # per-attempt decay + expected cost
markov-ci run examples/01-lint-error/config.yaml \
    --junit examples/01-lint-error/report.xml --seed 42
```

No API keys, no network — the default agent is a seeded, offline simulator. See the
[quick start](docs/quick-start.md) for the full five-minute path.

## How it works

A pipeline becomes a chain of decision states with three absorbing outcomes:

```
s0 verify ─▶ s1 triage ─▶ s2 agent ─▶ s3 sandbox ─▶ s4 regression ─▶ a1 ready-for-review
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

- Tutorials: [01 — lint fix](docs/tutorials/01-lint-error-first-pass.md) · [02 — decay → escalate](docs/tutorials/02-assertion-decay-escalation.md) · [03 — infra timeout](docs/tutorials/03-infra-timeout-no-tokens.md) · [04 — runner pools](docs/tutorials/04-runner-pool-sizing.md) · [05 — GitHub Actions](docs/tutorials/05-github-actions-e2e.md)
- How-to: [GitHub Actions](docs/how-to/integrate-github-actions.md) · [GitLab & Jenkins](docs/how-to/integrate-gitlab-jenkins.md) · [run the examples in Docker](docs/how-to/run-in-docker.md)

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
| **v0.1.0** | *Absorption* | Math core · policy engine · triage · simulated agent · guardrails · runtime · telemetry · CLI · demos 01–03 |
| **v0.2.0** | *Capacity & reach* | GitHub Action · queueing (Erlang-C + DES) · `simulate` · `recompute` · harness adapters (Claude Code, OpenCode, Aider) |
| **v0.3.0** | *Live operations* | MCP governance server · currency cost model · drift alerts · community harness templates |

Full ticket-level breakdown: [docs/WBS.md](docs/WBS.md).

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
