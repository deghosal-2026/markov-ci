# ADR-0014: "Markov-governed" means a planning model governing a bounded runtime

**Status:** Accepted
**Date:** 2026-11-17

## Context

The v0.1.1 review (FIX-05 §1 · PRD-01) found the documentation implies the runtime is
driven by the assembled Markov chain — "Markov-governed" reads as "the chain decides the
next hop". In fact the chain is a **planning/forecast** model: it predicts expected
attempts, token spend and outcome probabilities and sizes the caps. The runtime is a
bounded **retry governor**: it evaluates the gates in order (budget → attempt cap →
confidence) and stops on hard limits or terminal outcomes. The two were conflated, so
the headline claim overstated what the runtime does.

## Decision

We choose **A — reposition**, not "make the runtime chain-driven".

The **chain is the planning model**: `N = (I−Q)⁻¹`, `B = N·R`, `t = N·1`, `C = N·c`, and
the per-category priors, produce the forecast and the numbers the caps are sized from.
The **runtime is a bounded governor**: it admits, checks and stops a repair loop under
policy gates and guardrails; it does **not** sample the chain and does not claim to.

Vocabulary follows the split: **plan/forecast** for the model; **governor/govern** for
the runtime. The headline is reworded from "Markov-governed" to "Markov-planned"
(README, PRD-01, `docs/architecture.md`).

## Considered options

- **A — Reposition (chosen).** Keep the model as the planning/forecast layer; describe
  the runtime honestly as a bounded governor.
- **B — Make it true.** Drive the runtime loop from the assembled chain (sample the next
  hop from `P`). Rejected for v0.1.1: a large runtime rewrite whose only benefit over the
  governor is rhetorical, and it would put probabilistic state selection into a path where
  the guardrails, not the model, are the safety authority.

## Consequences

- Claims match the code: the model forecasts; the governor bounds. Both are testable
  (`analyze` output; gate/absorption tests).
- The tagline changes, so README/PRD/architecture must be rewired and the docs-consistency
  test (M12.19) will hold them together.
- **Falsifier:** if users genuinely need the runtime to follow the model — not merely be
  sized by it — option B returns as a v0.2 feature; ADR-0014 would then be superseded.
