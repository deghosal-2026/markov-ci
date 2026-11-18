# ADR-0010: Dual queueing model — Erlang-C estimate plus a discrete-event simulator

**Status:** Accepted
**Date:** 2026-11-16

## Context

Agentic repair changes the *shape* of CI load: human commits arrive in diurnal waves,
while agents fire bursty, recursive validation runs. Two facts make a single model
insufficient:

1. **M/M/c's assumptions are optimistic for agents.** Poisson arrivals and exponential
   service understate the tail when twenty agent loops fan out at 2 PM.
2. **Erlang-C does not directly give a p95.** It gives `P_wait` and the mean wait; the
   percentile needs the wait-time distribution (exact for M/M/c: an exponential tail).

At the same time, the closed form is genuinely useful: it is fast, transparent, and
correct *under its assumptions*, which is what most teams want for a first estimate.

## Decision

Ship **both**, clearly labeled:

- **Erlang-C** (spec 0009 §1) as the quick estimator, including the **exact p95** formula
  `ln(P_wait / 0.05) / (cμ − λ)`, with `λ ≥ cμ` rejected rather than answered.
- **A discrete-event simulator** (spec 0009 §2) for bursty arrival patterns and
  empirical service distributions, reporting p50/p95/p99.

The DES must converge to Erlang-C under Poisson input (a property test); under bursty
input the divergence is the finding, documented in the queueing explanation.

## Consequences

- Two implementations to maintain, and users must know which answer to trust — handled
  by `queue` printing the labeled estimate and the simulation side by side.
- The `queue` CLI and the demo 04 report must make the distinction obvious; both pools
  (human vs agent) are shown together.
- Invalid inputs are refused with guidance, never answered with a misleading number.
- **Falsifier:** if, across real adopters' telemetry, the DES and Erlang-C never
  materially diverge for agent traffic, the DES is complexity without value and should
  be demoted or dropped. The convergence property test is what keeps the two honest
  with each other.
