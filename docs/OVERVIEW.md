# markov-ci — The What and the Why (then the How)

> **Read this first.** This document explains what markov-ci is, the problem it addresses,
> why it's being created — and only after that, how it works.
> Product requirements: [prd/](prd/README.md) · Technical contract: [spec/](spec/README.md) ·
> Work plan: [WBS.md](WBS.md)

---

## What this is

`markov-ci` is an open-source toolkit for running **AI agents inside CI/CD pipelines
without losing control of cost, time, or code quality**.

It ships as three things:

- a **Python library** (`markov_ci`) implementing the governance model,
- a **CLI** (`markov-ci`) that forecasts, simulates, and executes governed pipelines,
- a **GitHub Action** (`action.yml`) that plugs the same engine into GitHub Actions.

You describe your pipeline as a probabilistic state machine — a Markov chain — give it
measured or estimated success/failure probabilities, and markov-ci then does three
things for you:

1. **Forecasts.** Before you enable anything, it computes the expected number of agent
   attempts, token spend, and runner-minutes per build.
2. **Governs.** At runtime it enforces hard, mathematical limits — an agent cannot loop
   forever, cannot exceed budgets, cannot touch forbidden files, cannot weaken your
   tests, and can never auto-merge to main.
3. **Learns.** Every state transition is recorded as structured telemetry, and the
   probabilities are recomputed from real production data as your system runs.

## The problem it addresses (why)

**CI/CD stopped being deterministic, but our tooling still pretends it is.**

For fifteen years a pipeline was a Directed Acyclic Graph: same commit in, same result
out. Two forces broke that assumption:

1. **Ephemeral infrastructure and shared fleets.** Distributed test suites, cloud
   runners, and spot instances mean identical builds now pass or fail on network jitter
   and CPU contention.
2. **AI agents in the loop.** Agents now triage failures, patch broken tests, and
   refactor code *inside* pipelines. They are probabilistic by nature: an agent might
   fix a build failure 75% of the time, get stuck in a hallucination loop 15% of the
   time, and introduce a regression 10% of the time.

When you govern a probabilistic system with rigid `if/else` YAML, you get one of two
failures — guardrails so strict the agent never helps, or so loose that it runs wild.

In practice, teams already feel this as:

- **Runaway cost** — an agent retries an unsolvable failure overnight; the cloud bill
  and token spend arrive as a surprise.
- **Lost developer flow** — engineers watch hung PRs or wait in queues because agents
  saturated the runner pool.
- **Silently weakened tests** — an agent "fixes" a failing test by loosening the
  assertion. The build is green; the test suite's signal is gone.
- **No forecasts, no answers** — "should the agent get 2 retries or 10?" is answered by
  gut feeling, because no model of the pipeline produces the number.
- **Unbounded escalation** — nothing defines when an agent should give up and hand
  control back to a human.

## Why it's being created

1. **Timing.** Agents are entering CI *right now*, and every team wiring an LLM into a
   build pipeline faces the same governance vacuum. The closest existing tools are
   blind retry actions (no probability model), agent harnesses (act, but don't
   govern), and prompt guardrails (validate text, not pipelines).
2. **The math already exists.** Absorbing Markov chains have modeled "systems that move
   between states and eventually terminate" for decades. A pipeline is precisely such
   a system. It has simply never been packaged as reusable CI/CD infrastructure.
3. **It's measurable.** Production telemetry gives real numbers to feed the model —
   e.g., most PRs pass without agent intervention (~82%); most failures are
   agent-repairable (~75%); success probability decays with each attempt. A model built
   on those numbers can be tested, calibrated, and falsified — unlike superstition.
4. **It must be shared, not re-invented.** Without a central framework, every team
   writes its own fragile retry YAML, and every organization re-learns the same
   runaway-loop incident.

## The core idea (one line)

> **Stop treating a pipeline as a fixed graph. Treat it as an absorbing Markov chain —
> states, measured transition probabilities, and guaranteed terminal exits — then turn
> those computed expectations into runtime guardrails.**

"Absorbing" means every run terminates in one of three designed outcomes — never in an
infinite loop:

| Absorbing state | Meaning |
|---|---|
| `a1_ready_for_human_review` | Build is green; a human reviews and merges |
| `a2_escalate_to_author` | Agent gives up; returns control to the developer with diagnostics |
| `a3_budget_exceeded` | Hard stop: token, time, or step budget tripped |

## How it works

Five steps, in order. (Full technical contract: [spec/](spec/README.md); math:
[explanations/markov-model.md](explanations/markov-model.md).)

### 1. Define the pipeline as states

Instead of a tangled graph of jobs, you declare a small set of decision states:

```
s0 deterministic verify → s1 failure triage → s2 agent reasoning
  → s3 sandbox validation → s4 regression check
        ↘ loop: s3 can send the agent back around with new error logs
absorbing: a1 ready-for-review · a2 escalate · a3 budget-exceeded
```

### 2. Attach probabilities

Each edge carries a probability — from your telemetry if you have it, from bundled
conservative priors if you don't. Attempt history is encoded *in the state name*
(`s2#1`, `s2#2`, `s3#3`), which keeps the model mathematically honest while letting
success probability decay per attempt.

### 3. Compute expectations before rollout

From the transition matrix, markov-ci computes:

- **N = (I − Q)⁻¹** — expected visits to each state (how many agent attempts?),
- **B = N·R** — probability of each outcome (how often do we escalate?),
- **C = N·c** — expected cost per run (tokens, runner-minutes, wall clock).

This turns "how many retries?" from a debate into a calculation. On the bundled default
matrix: ~92% of PRs reach ready-for-review, ~73% of agent-eligible failures get resolved,
and an infra flake is predicted to waste zero tokens.

### 4. Run with enforced guardrails

At runtime the engine checks, in order: budget → step cap → confidence threshold. A patch
is only applied if it passes an allowlist (agents may write `src/` and `tests/`, never
`.github/` or secrets), a test-modification check (weak assertions = hard stop), and a
sandbox test run. Patches go to an isolated `ai-fix/pr-<n>` branch — never the PR branch,
never force-pushed, never auto-merged.

### 5. Learn from telemetry

Every hop emits one structured JSON event (`from_state`, `to_state`, `duration_ms`,
`tokens_used`, …). Feed the events back and the transition matrix is recomputed — the
guardrails adapt to your actual agents, codebase, and models as they change.

## What you get

- A reusable **library, CLI, and GitHub Action** (Apache-2.0)
- **Five working demos**, all runnable offline with zero API keys
- **Complete docs**: tutorials, how-tos, math derivations, reference, ADRs
- **3–4 published articles** (Dev.To + LinkedIn) explaining the model

## What it is not

- ❌ Not an **agent harness** — it governs agents; it doesn't host them
- ❌ Not **auto-merge** — `a1` is *ready for human review*, always
- ❌ Not a **CI replacement** — it plugs into GitHub Actions, GitLab, Jenkins
- ❌ Not a **dashboard** — CLI + JSON events; build your own views

## Where to go next

[Quick start](quick-start.md) · [Architecture](architecture.md) ·
[The math, derived](explanations/markov-model.md) · [PRD](prd/README.md) · [spec](spec/README.md)
