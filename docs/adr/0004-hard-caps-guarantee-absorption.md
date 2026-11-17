# ADR-0004: Hard caps guarantee absorption by construction

**Status:** Accepted
**Date:** 2026-11-16

## Context

Empirical matrices can be wrong — adversarially or accidentally. If a loop-back edge
carries probability ~1 and exit probability ~0, `I − Q` is singular, `N` does not
exist, and the "runaway loop" incident is back. Policing loops at runtime (timeouts,
kill scripts) treats the symptom after money is burned.

## Decision

At assembly time, `max_attempts` removes the final loop-back edges and re-normalizes
that mass into designed absorbing states. Every chain markov-ci can execute is
therefore absorbing *by construction* — `I − Q` invertible, absorption guaranteed, no
matter what the priors say.

## Consequences

- Runaway loops are mathematically impossible, not merely discouraged.
- Budgets (tokens, wall-clock) are a second, independent stop (spec 0004).
- Caps are visible in the matrix, so `analyze` shows the user exactly where their
  runs will stop.
- Falsifier: an e2e test feeds `success = [1.0, 1.0, 1.0]` and asserts termination.
