# ADR-0002: Encode attempt count in the state name

**Status:** Accepted
**Date:** 2026-11-16

## Context

Agent success probability decays per attempt, and attempt history matters ("agent
already tried twice" changes the odds). A plain Markov chain is memoryless; the
common industry fix — decaying a probability table per retry step — makes the chain
*time-inhomogeneous*, silently breaking the `N = (I−Q)⁻¹` math the whole model rests on.

## Decision

We expand loop-capable states into attempt-indexed states (`s2_agent_reasoning#1`,
`s2#2`, `s3#1`, …) up to `policy.max_attempts`, with per-attempt edges resolved from
priors. Attempt history lives in the state, not in hidden counters.

## Consequences

- The chain stays genuinely Markov — all closed-form results remain exact.
- State-space growth is bounded by `max_attempts` (default 3) — negligible.
- Per-attempt decay is expressed as ordinary edges; no special-case code.
- Falsifier: if telemetry shows within-attempt behavior still depends on unmodeled
  history, we add dimensions the same way (state augmentation), never hidden state.
