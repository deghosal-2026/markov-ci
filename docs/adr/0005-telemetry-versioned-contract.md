# ADR-0005: Telemetry is a schema-versioned JSONL contract

**Status:** Accepted
**Date:** 2026-11-16

## Context

The model is only as good as its probabilities, so probabilities must come from
production data — meaning events must be complete, stable, and machine-processable
forever. Ad-hoc logging drifts and quietly breaks the recompute path.

## Decision

Every state transition emits exactly one JSON object (JSONL, append + flush) validated
against `schemas/transition-event.schema.json`, versioned by `schema_version`. Events
must alone be sufficient to recompute the matrix — per *(failure category × adapter)*
— and must never contain secrets.

## Consequences

- `recompute` is a pure function of the event stream; the governance loop closes.
- Schema evolution is explicit (bump + accept-older policy, spec 0012).
- Third parties (warehouses, dashboards) can build on the contract without us
  building a UI (a stated non-goal).
- Falsifier: a round-trip golden test — events → recompute → posterior reproduces
  analytic results within credible intervals.
