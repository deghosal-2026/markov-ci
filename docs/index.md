# markov-ci

**Markov-planned, guardrailed CI/CD.**

> **Status: pre-1.0.** The CLI, config, and telemetry contracts on this site
> (golden numbers included) are implemented and executed in CI — docs-are-tests.
> `v0.1.1` ("Trust") is the current release; **upgrade from `v0.1.0`** (harness
> shell-injection advisory, ADR-0016). The public API is not yet stable.

CI/CD pipelines have become probabilistic: ephemeral infrastructure flakes identical
builds, and AI agents embedded in pipelines fix, loop, and regress probabilistically.
`markov-ci` stops treating pipelines as deterministic DAGs and models them as what they
are — **absorbing Markov chains** — then turns that model into three capabilities:

| Capability | What you get |
|---|---|
| **Forecast** | Expected agent attempts, token spend, and outcome probabilities per failure category — *before* you enable anything (`N = (I−Q)⁻¹`, `B = N·R`, `C = N·c`) |
| **Govern** | Budgets, attempt caps, and confidence gates that make runaway loops mathematically impossible; enforced allowlists; test-weakening hard-stopped; patches isolated to `ai-fix/*` branches; humans merge — never agents |
| **Learn** | Every state transition emits a versioned JSONL event; the transition matrix recomputes from your own telemetry, per failure category and per agent harness |

**Why it can't run away:** attempt caps remove loop-back edges at assembly time, so
every chain markov-ci can execute is absorbing *by construction* — after the cap `Q` is
nilpotent. The runtime stops via its attempt counter and per-call timeouts.

## Try it in five minutes

```bash
pip install -U "markov-ci>=0.1.1"
markov-ci analyze          # zero-config: prints the worked example
```

Then follow the [quick start](quick-start.md) or jump straight into the
[tutorials](tutorials/01-lint-error-first-pass.md) — all offline, zero API keys.

## Where to go

- [Quick start](quick-start.md) — first forecast in five minutes
- [Architecture](architecture.md) — modules and data flow
- [The math, derived](explanations/markov-model.md) — where `N`, `B`, `t`, `C` come from
- [Config](reference/configuration.md) · [Telemetry](reference/telemetry.md) · [CLI](reference/cli.md)
- [What & why, in depth](OVERVIEW.md) · [Design decisions](adr/README.md)
