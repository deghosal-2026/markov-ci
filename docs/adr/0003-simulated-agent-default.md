# ADR-0003: The default agent is offline, deterministic, and simulated

**Status:** Accepted
**Date:** 2026-11-16

## Context

The product's demos, tests, and first-run experience must be reproducible: same input →
same output, zero API keys, zero network. Real LLMs make all three impossible and put
token spend between a curious user and the value.

## Decision

`SimulatedAgent` (seeded, fixture-driven, calibrated so observed outcomes match the
priors statistically) is the default adapter. Real harnesses are opt-in extras
(ADR-0007).

## Consequences

- Every demo and CI job runs offline and byte-stable under `--seed`.
- Golden tests can assert exact absorbing states and event streams.
- A simulated agent calibrated to priors lets users *feel* the model before wiring a
  real one — the forecast and the demo tell the same story.
- Risk: simulated calibration flatters the priors; the fix is honest labeling
  (`adapter: simulated`) and empirical recompute when real adapters arrive.
