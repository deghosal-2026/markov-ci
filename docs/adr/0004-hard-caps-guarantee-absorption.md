# ADR-0004: Caps make every assembled chain acyclic (nilpotent `Q`)

**Status:** Accepted
**Date:** 2026-11-16

## Context

Empirical matrices can be wrong — adversarially or accidentally. A loop-back edge whose
exit probability is *near* zero makes `I − Q` ill-conditioned, and *exactly* zero makes it
singular; either way `N` is meaningless and the "runaway loop" incident is back. Runtime
policing (timeouts, kill scripts) is still required for the live system, but it is not a
*structural* guarantee — it stops a run after resources are spent and does not bound what
the matrix says.

## Decision

At assembly time, `max_attempts` removes the final loop-back edges and re-normalizes that
mass into the designed absorbing state — **`a2_escalate_to_author`** when the attempt cap
is reached, **`a3_budget_exceeded`** when a budget is exhausted (spec 0002 §4, spec 0004,
spec 0011 §1). Every chain markov-ci can execute is therefore acyclic *by construction* —
`Q` is nilpotent, absorption is guaranteed, no matter what the priors say.

The **runtime bound is separate and is not a theorem:** a live run stops because of the
attempt-counter gate (spec 0004 §2) and per-call subprocess timeouts (spec 0006 §3,
spec 0011). Both are stated; neither is claimed to be unnecessary.

## Considered options

- **Runtime timeouts / kill scripts.** Rejected: they police the symptom *after* money and
  time are burned; the run is not bounded in advance.
- **Reject any matrix with a near-1 loop-back probability.** Rejected: brittle, and it
  refuses legitimate high-retry pipelines instead of bounding them.
- **Delete loop-back edges at assembly time (chosen).**

## Consequences

- Runaway loops are mathematically impossible **in the model**, not merely discouraged.
- The **model** is acyclic after the cap (`Q` nilpotent): absorption is a property of the
  chain, not a promise that a wedged child process exits on its own.
- The **runtime** stops via its attempt counter plus per-call timeouts; budgets (tokens,
  wall-clock) are a second, independent stop (spec 0004).
- Caps are visible in the matrix, so `analyze` shows the user exactly where their
  runs will stop.
- **Falsifier:** a property test over a random `Q` with arbitrary loop-back mass
  (including exactly `1.0`) *and* random user-declared edges asserts that assembly yields
  a nilpotent `Q` or a validation error — an e2e `success = [1, 1, 1]` test alone would
  pass even with no cap.
