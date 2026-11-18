# Spec 0002 — Matrix assembly and the math module

**Status:** Stable (v0.1 contract) · **Amends:** — · **Implements:** PRD F2, F3

## 1. Assembly

Given base states, base edges, priors, `max_attempts`, the observed failure category,
and the active adapter, `assemble()` builds the canonical chain:

1. **Expand states** (spec 0001 §2). Order: transients first, absorbing last.
2. **Fill edges:** static edges from spec 0001 §3; per-attempt edges resolved from
   `priors[adapter][category]`.
3. **Force caps:** `s2#max_attempts` and `s3#max_attempts` lose their loop-back edges;
   the freed probability mass re-normalizes into `a2`/`a3` (spec 0004 §2).
   *This step is the absorption guarantee* — see ADR-0004.
4. **Validate:** every transient row sums to 1 (|Σp − 1| ≤ 1e-9); every absorbing row is
   the identity; every transient state reaches an absorbing state.

Output: canonical form `P = [[Q, R], [0, I]]` with `Q` (t×t) and `R` (t×r).

## 2. Math module (`markov_ci.model`)

Pure functions over numpy arrays; fully typed; property-tested (spec 0012 §3).

| Function | Signature | Returns |
|---|---|---|
| `validate` | `(P) -> ValidationResult` | row sums, reachability, absorbing rows |
| `split` | `(P, transient, absorbing) -> (Q, R)` | canonical form |
| `fundamental` | `(Q) -> N` | `N = (I − Q)⁻¹` — expected visits per transient state |
| `absorption` | `(N, R) -> B` | `B = N·R` — P(absorb in j \| start in i) |
| `steps_to_absorb` | `(N) -> t` | `t = N·1` — expected hops to absorption |
| `expected_cost` | `(N, c) -> C` | `C = N·c` — expected cost per start state |
| `posterior` | `(counts, prior, alpha) -> (P̂, ci)` | Dirichlet posterior + credible interval |

## 3. Cost vectors

`c` is a per-state cost vector (tokens, runner-seconds, or unit weights).
`C = N·c` is the forecast API behind `analyze --json` (PRD US-1, US-9) and the FinOps
baseline that `recompute` (spec 0007) later compares against actuals.

## 4. Invariants (property tests, must always hold)

- `B` rows sum to 1 (every run absorbs somewhere).
- `N ≥ 0`; `t` finite and positive.
- `expected_cost` monotone in `c`.
- Matrix recomputed from a telemetry event stream reproduces `B` within its credible
  interval (round-trip test).
- Absorption holds under adversarial inputs: even a prior of `success = [1.0, 1.0, 1.0]`
  must terminate (caps → `a3`/`a2`).

## 5. Worked example (golden numbers, default priors)

With the default structural edges (`s2→s3 = 0.95`) and the shipped cap
`max_attempts = 3`: **P(a1 | s2) ≈ 0.72**, **P(a1 | s0) ≈ 0.92** (the uncapped limit is
0.729). These are golden-test values; docs and tutorials must not drift from them.
