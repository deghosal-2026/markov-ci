# Spec 0001 — State model

**Status:** Stable (v0.1 contract) · **Amends:** — · **Implements:** PRD F1

## 1. Base states (default pipeline)

| ID | Type | Meaning |
|---|---|---|
| `s0_deterministic_verify` | transient | Fast checks: lint, compile, unit tests |
| `s1_failure_triage` | transient | Deterministic log classification |
| `s2_agent_reasoning` | transient | Agent inspects diff + context, proposes patch |
| `s3_sandbox_validation` | transient | Patch applied in isolation; failing tests re-run |
| `s4_regression_check` | transient | Full suite + static analysis on patched branch |
| `a1_ready_for_human_review` | **absorbing** | Green build + patch summary posted for human sign-off |
| `a2_escalate_to_author` | **absorbing** | Agent cannot proceed (probability/budget); control returns to developer |
| `a3_budget_exceeded` | **absorbing** | Hard guardrail tripped (tokens/wall-clock/steps) |

**Absorbing-state invariant:** once entered, `P(stay) = 1`. No transition may leave an
absorbing state; the engine enforces this at assembly time (spec 0002).

## 2. Step augmentation

Config declares base states and `policy.max_attempts` (default 3). The loader expands
loop-capable transient states into attempt-indexed states:

```
s2_agent_reasoning    → s2_agent_reasoning#1, s2_agent_reasoning#2, …, #max_attempts
s3_sandbox_validation → s3_sandbox_validation#1, …, #max_attempts
```

- String form: `name#attempt`. Internal form: `(name, attempt)`.
- Loop-back edges `s3#k → s2#(k+1)` carry **per-attempt probabilities** (§4 of this spec).
- Non-loop states (`s0`, `s1`, `s4`) are singletons.
- Rationale: this keeps the chain genuinely Markov while modeling per-attempt decay —
  the fix for time-inhomogeneous "decay hack" probability tables. See ADR-0002.

## 3. Base transition probabilities (defaults, field-test literature)

| from | to | p | note |
|---|---|---|---|
| `s0` | `a1` | 0.82 | pass without agent |
| `s0` | `s1` | 0.18 | some failure |
| `s1` | `s2` | 0.75 | eligible for agent repair |
| `s1` | `a2` | 0.25 | infra outage / complex break — never agent |
| `s2#k` | `s3#k` | `prior.success[k]` | valid patch (per category × adapter, per attempt) |
| `s2#k` | `a2` | remainder | context limit, invalid output |
| `s3#k` | `s4` | 0.65 | patch fixed immediate failure |
| `s3#k` | `s2#(k+1)` | 0.25 → decays per attempt | loop back with new error logs |
| `s3#k` | `a2` | 0.10 | hard stop (e.g., patch deletes a test) |
| `s4` | `a1` | 0.90 | regression clean |
| `s4` | `a2` | 0.10 | secondary regression — abort, escalate |

## 4. Priors: keyed by failure category × adapter

Observed agent behavior differs **per harness** (same model, different harness: token
use has been observed to vary ~70×). Priors are therefore two-dimensional, with a
`default` fallback used when no adapter-specific data exists:

```yaml
priors:
  default:                        # adapter "*" — the shipped conservative priors
    default:        { success: [0.95, 0.95, 0.95], cost_weight: 1.0 }
    lint_error:     { success: [0.92, 0.65, 0.20], cost_weight: 1.0 }
    type_mismatch:  { success: [0.85, 0.55, 0.25], cost_weight: 1.5 }
    unit_assertion: { success: [0.74, 0.45, 0.15], cost_weight: 2.5 }
    infra_timeout:  { success: [0.05, 0.01, 0.00], cost_weight: 5.0 }
  claude-code:                    # adapter-specific, once telemetry exists
    unit_assertion: { success: [0.71, 0.42, 0.12], cost_weight: 3.1 }
```

- Resolution order: `priors[adapter][category]` → `priors["default"][category]` → error.
- `success[k]` = P(patch valid on attempt k); `cost_weight` scales the per-state cost
  vector for `C = N·c` (spec 0002 §3).
- Every prior must be labeled `source: prior` or `source: empirical` in config; empirical
  entries are produced by `recompute` (spec 0007 §4) and carry credible intervals.

Infra timeouts are near-zero by design: the `min_confidence` gate (0.40) rejects them on
attempt 1, spending zero tokens.
