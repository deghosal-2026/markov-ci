# Quick start

> **Pre-alpha.** The commands below are the v0.1.0 CLI contract (spec 0008),
> implemented and run verbatim in CI — docs-are-tests.

Time to first forecast: **5 minutes. Zero API keys. Zero network.**

## 1. Install

```bash
git clone https://github.com/deghosal-2026/markov-ci && cd markov-ci
pip install -e ".[dev]"
```

Requires Python 3.11+.

## 2. First forecast — zero config

```bash
markov-ci analyze
```

Out of the box this loads the packaged default state space + priors (spec 0003 §3) and
prints the worked example:

```text
markov-ci analyze — default pipeline
states: 5 transient · 3 absorbing (a1, a2, a3)

Absorption probabilities (start: s0_deterministic_verify)
  a1_ready_for_human_review   ≈ 0.92
  a2_escalate_to_author       ≈ 0.07
  a3_budget_exceeded          —  (policy caps not tripped at forecast time)

Expected steps to absorption: t = N·1
Expected cost (cost_weight units): C = N·c
```

The two golden numbers — **P(a1 | s0) ≈ 0.92** and **P(a1 | s2) ≈ 0.72** — are asserted
by the test suite; if your build prints different values, the build is wrong.

## 3. Per-category forecast

```bash
markov-ci analyze --category unit_assertion
```

Shows per-attempt decay (priors `[0.74, 0.45, 0.15]`), expected attempts, and expected
cost — the number that ends the "2 retries or 10?" debate.

## 4. Validate your own pipeline

```bash
markov-ci validate config.yaml        # exit 0 = matrix valid, 4 = invalid (with the offending row)
```

## 5. Run a governed demo — still offline

```bash
git -C examples/01-lint-error/repo init -q && \
  git -C examples/01-lint-error/repo add -A && \
  git -C examples/01-lint-error/repo commit -qm "demo baseline"

markov-ci run examples/01-lint-error/config.yaml \
  --junit examples/01-lint-error/report.xml \
  --repo examples/01-lint-error/repo --seed 42
echo $?    # 0 = absorbed in a1 (ready for human review)
```

The simulated agent is the default adapter — no keys, byte-stable under `--seed`.
The event stream lands in `examples/01-lint-error/.markov-ci/events.jsonl` (see
[reference/telemetry](reference/telemetry.md)).

## Where next?

- [Tutorial 01](tutorials/01-lint-error-first-pass.md) — walk that run hop by hop
- [Run the examples in Docker](how-to/run-in-docker.md) — reproducible, zero setup
- [Adoption ladder](prd/12-launch-and-gtm.md) — Observe → Stress → Govern → Learn
- [Configuration reference](reference/configuration.md) — your own states and priors
