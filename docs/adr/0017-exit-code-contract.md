# ADR-0017: Exit codes are the outcome contract — a2 moves off Click's reserved 2

**Status:** Accepted
**Date:** 2026-11-17
**Supersedes:** the v0.1.0 exit-code contract in spec 0008

## Context

The v0.1.1 review (FIX-03 §6 · DES-29) found the run exit code doubles as the
absorbing-state contract, but `a2` used `2` — the code **Click reserves for usage
errors**. A mistyped flag and an escalated run were indistinguishable to CI. Uncaught
exceptions produced Click's generic error code, which had no documented meaning, and the
`BY_CODE` map in `action/run.sh` could silently disagree with the CLI.

## Decision

Each terminal outcome has **exactly one** code, and CI may branch on it:

| Code | Meaning |
|---|---|
| `0` | absorbed in `a1_ready_for_human_review` (or clean validation) |
| `1` | absorbed in `a2_escalate_to_author` |
| `2` | **reserved** — CLI usage error (Click); never a run outcome |
| `3` | absorbed in `a3_budget_exceeded` |
| `4` | invalid config / input — always explained, never silent |
| `5` | internal / infrastructure failure |

Every exception is caught at the CLI boundary and mapped to a documented code **and a
terminal event** (spec 0007); a run never exits with a bare traceback. The `BY_CODE` map
in `action/run.sh` mirrors this table exactly.

This is a **breaking change** to the v0.1.0 contract: `a2` moves `2 → 1`, and `2` becomes
the usage-error code. It is recorded in the CHANGELOG.

## Considered options

- **Move `a2` to `1`, add `5` for internal failure (chosen).** Uses the low codes that
  `0`/`3`/`4` already occupied; `2` goes back to Click.
- **Keep `2` for `a2` and disambiguate by output channel.** Rejected: a code that means
  two things is not a contract, and CI should not parse prose.
- **A single non-zero "failed" code for everything.** Rejected: the absorbing state is
  the product's core signal — CI must be able to tell escalation from a budget stop.

## Consequences

- CI branches unambiguously: `0` merge-ready, `1` human required, `3` budget hit, `4`
  bad input, `5` infra — with `2` safely Click's.
- The change is breaking; the CLI reference, `action.yml`, spec 0008 and the CHANGELOG
  all state it (M12.6), and the code lands in M13.37.
- **Falsifier:** if a future outcome cannot be expressed without overloading a code, the
  contract is amended by a new ADR — never by reusing a reserved code.
