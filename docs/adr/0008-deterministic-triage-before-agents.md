# ADR-0008: Deterministic triage before any agent runs

**Status:** Accepted
**Date:** 2026-11-16

**Review note (v0.1.1).** The routing taxonomy lives in spec 0010, not here; this ADR owns
only the *principle* (deterministic triage before any agent). Two honest caveats: failures
routed away never get an attempt, so their fixability is never observed (the falsifier
needs a shadow/exploration mode); and `unknown` requires a prior to opt in, which spec 0003
does not currently supply.

## Context

Agents are expensive and unreliable on non-code failures. Routing an AWS spot
interruption, a registry 503, or a network timeout to an LLM cannot fix it and wastes
tokens, latency, and attention. Field data supports this: the prior probability of an
agent repairing an `infra_timeout` is ~0.05 and decaying to zero.

This is principle #5 of the product ("determinism before intelligence"): nothing
reaches an agent before a deterministic classifier has categorized it.

## Decision

Every failure passes a deterministic, rule-based classifier (spec 0010) before any
adapter is invoked. The taxonomy is
`{lint_error, type_mismatch, unit_assertion, infra_timeout, dependency_error, unknown}`.
`infra_timeout` and `dependency_error` route directly to `a2_escalate_to_author` with
**zero tokens**. `unknown` also escalates unless a user explicitly opts in.

## Consequences

- Failures that cannot be code-fixed never cost a cent.
- The classification taxonomy and its signature table become maintained artifacts.
- `unknown` defaults to escalation (the safe direction), which may be conservative for
  exotic-but-fixable failures until signatures are added.
- Triage stays rule-based — no ML, no randomness, fully deterministic and testable.
- **Falsifier:** if telemetry shows the cost of misclassified (routed-away) failures
  exceeds the tokens saved, revisit the taxonomy and routing. The events carry
  `failure_category`, so this is measurable rather than a matter of opinion.
