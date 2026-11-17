# ADR-0001: Model agentic CI/CD pipelines as absorbing Markov chains

**Status:** Accepted
**Date:** 2026-11-16

## Context

Agents in CI make pipeline behavior probabilistic (fix ~75% / loop ~15% / regress ~10%
is typical). Deterministic if/else governance of such systems produces either useless
agents or runaway loops, and cannot answer "2 retries or 10?" with data. Pipelines are
finite-state systems that terminate — exactly the shape absorbing Markov chain theory
describes.

## Decision

We model the pipeline as an absorbing Markov chain: a small decision-boundary state
space, measured transition probabilities, and three designed terminal states
(`a1_ready_for_human_review`, `a2_escalate_to_author`, `a3_budget_exceeded`), and we
compute expectations from the matrix rather than guessing policies.

## Consequences

- Forecasts become closed-form: `N = (I−Q)⁻¹`, `B = N·R`, `t = N·1`, `C = N·c`.
- Termination guarantees become structural, not procedural (see ADR-0004).
- We must maintain probabilities from telemetry (ADR-0005) — a stale matrix is the
  new failure mode; drift detection is the falsifier.
- We accept the Markov property's constraints and handle them explicitly (ADR-0002).
