# ADR-0009: Guardrails are enforced in code, never delegated

**Status:** Accepted
**Date:** 2026-11-16

## Context

Safety instructions to an agent — "do not modify CI files", "do not weaken tests" —
are suggestions, not guardrails. Likewise, a harness's own allowlist or auto-accept
setting is not a control markov-ci owns. The most damaging observed anti-pattern is an
agent "fixing" a failing test by loosening the assertion: the build turns green and the
test suite's signal is destroyed.

Principles #3 (guardrails are code), #7 (governance is never delegated), and #8 (humans
merge) all point the same way.

## Decision

The following are implemented and enforced in the engine, applied to every patch
regardless of adapter:

1. **Write allowlist** (default `src/**`, `tests/**`) with an **always-denied set**
   (`.github/**`, `.git`, `*.env`, `**/secrets/**`, CI configs, lockfiles, `LICENSE`)
   that user configuration **cannot widen**.
2. **Test-modification-ratio hard stop** — `tmr > 1.0` or any assertion deletion
   escalates to `a2` and sets `mandatory_review`.
3. **Branch isolation** — patches only to `ai-fix/pr-<n>`; the PR branch and `main` are
   never touched.
4. **No force-push** — no such code path exists anywhere.
5. **No auto-merge** — `a1_ready_for_human_review` is terminal; merging is human work.

Harness/host settings are additive defense only; they never substitute for these.

## Consequences

- Safety becomes **testable**: adversarial fixtures assert every rule.
- Some flexibility is deliberately removed — the always-denied set is not configurable,
  by design.
- TMR can produce false positives on legitimate test changes; the reviewer sees the
  ratio and the diff and can approve deliberately. Friction is placed where it belongs.
- **Falsifier:** any confirmed bypass of a guardrail is a security-class bug: add a
  regression test, fix the rule, and record it. If TMR's false-positive rate becomes a
  real burden, the threshold is tunable — the hard stop is not.
