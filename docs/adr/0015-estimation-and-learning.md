# ADR-0015: Estimation and learning — smoothed per-attempt curves, honest about censoring

**Status:** Accepted
**Date:** 2026-11-17

## Context

Telemetry alone must be able to rebuild the model (spec 0007 §4, spec 0002 §2). The
v0.1.1 review (FIX-05 §4 · SRC-08, DES-12) found the estimation path was ambiguous: it
was not pinned which quantity maps to which edge, the CLI did not pass the config prior
or `alpha`, simulated events were mixed with real ones, gate rejections were not
recorded, and `recompute` was not demonstrably idempotent. Cold start, censoring and
drift were argued case by case rather than decided.

## Decision

1. **Priors.** A per-`(adapter, category)` **per-attempt success curve**. Shipped priors
   are **illustrative, not measured** (M12.9). Cold start falls back to the labelled
   prior.
2. **Prior strength.** A single `alpha` (prior concentration in pseudo-counts) per
   estimate, default `1.0`; the CLI passes the config prior and `alpha` through.
3. **Hierarchical pooling.** Estimates pool **per category** and **per harness**
   (`adapter`); a missing `(adapter, category)` block falls back to `default`. Per-harness
   learning is real once the harness id is set (M13.19, M13.31).
4. **Exactly one edge per quantity.** Each estimated success probability maps to
   **exactly one** edge — `P(s4 reached | s2#k entered)`, i.e. the `s2#k → s3` attempt and
   the `s3#k → s4` validation — never estimated twice or from two different edges.
5. **Censoring.** A run that never reaches `s4` is a **right-censored** observation, not a
   failure: it counts in the denominator, not the numerator. Data from a **gate
   rejection** is excluded from success estimation and recorded as `gate_rejected` with a
   reason.
6. **Synthetic data.** Simulation events carry `synthetic: true` and are **excluded by
   default**; `recompute` never mixes simulated and real counts.
7. **Drift / windowing.** v0.1.1 records `config_hash` and `model_version` on every
   event. Windowing is done by **selecting which events** feed `recompute` — the model
   does not silently down-weight old data. Automatic drift detection is v0.3 (M11.5).
8. **Idempotent `recompute`.** `recompute(events, alpha, prior)` is a pure function of its
   inputs: same inputs → byte-identical output; no hidden state, no writes.

## Considered options

- **Beta-Binomial per attempt, via the Dirichlet generalization** in `model.posterior`.
  Chosen: one smoothing mechanism, credible intervals for free, no SciPy dependency.
- **Raw frequency, no smoothing.** Rejected: cold start and thin samples give 0/1 spikes
  that make forecasts and cap sizing lie.
- **Exponential time-decay weighting.** Rejected for v0.1.1: there is no drift detector
  yet, so a decay constant would be a guess. Windowing by explicit event selection is
  testable now; revisit when M11.5 lands.

## Consequences

- Forecast numbers come with their uncertainty, and cold start uses labelled priors.
- The censoring rule stops "no patch was produced" from inflating apparent failure.
- `recompute` is safe to run repeatedly and to compare (byte-stable).
- **Falsifier:** if windowing by selection proves insufficient once drift detection
  exists (M11.5), a time-decay weight is added and this ADR is superseded.
