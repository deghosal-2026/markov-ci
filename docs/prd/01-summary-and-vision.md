# 01 — Executive summary, vision, positioning

## Executive summary

CI/CD pipelines have become probabilistic — ephemeral infrastructure makes identical
builds flake, and AI agents embedded in pipelines fail, loop, and regress
probabilistically. Yet pipelines are still governed by deterministic if/else rules, which
produces either useless agents or runaway loops, surprise token bills, weakened test
suites, and no way to answer "how many retries should the agent get?" with data.

`markov-ci` is an open-source Python library + CLI + GitHub Action that models an
agentic pipeline as an **absorbing Markov chain**: a small state space, measured
transition probabilities, and three guaranteed terminal outcomes (ready-for-human-review,
escalate-to-author, budget-exceeded). From that model it **forecasts** cost/attempts
before rollout (`N = (I−Q)⁻¹`, `B = N·R`, `C = N·c`), **governs** the live pipeline with
hard budget/cap/confidence guardrails and enforced least-privilege rules, and **learns**
by recomputing the matrix from structured telemetry.

**The one-sentence product test:** a platform engineer can, in under five minutes and
with zero API keys, forecast what an agent-allowed pipeline will cost and then run a
governed demo that provably cannot run away.

## Vision

Every agentic pipeline ships with a probability model and hard absorbing boundaries,
the way every service ships with a health check.

## Tagline

*Markov-governed, self-healing CI/CD.*

## Positioning statement

For platform engineers adding AI agents to CI/CD, markov-ci is the governance layer
that forecasts and bounds agent behavior; unlike retry actions and agent harnesses, it
computes what agents will cost and guarantees they cannot run away — while humans stay
accountable for every merge.
