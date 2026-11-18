# The Markov model, derived

Where every number markov-ci prints comes from. No prior Markov knowledge assumed.

## 1. The chain, in pipeline terms

A **Markov chain** is a system that hops between discrete states, where
P(next hop) depends only on the current state:

```
P(Xₙ₊₁ = j | Xₙ = i, everything before) = P(Xₙ₊₁ = j | Xₙ = i)
```

A pipeline *is* this: `s0 verify → s1 triage → s2 agent → s3 worktree validation → s4 regression`,
ending in one of three **absorbing states** — `a1 ready-for-human-review`,
`a2 escalate-to-author`, `a3 budget-exceeded`. Absorbing means `P(stay) = 1` forever.

Order all states transients-first and the transition matrix takes the **canonical
form**:

```
      ⎡ Q  R ⎤        Q: transient → transient  (t×t)
P  =  ⎣ 0  I ⎦        R: transient → absorbing (t×r)
                     I: absorbing identity
```

## 2. The four results we productize

**Fundamental matrix.** From any transient state the run visits transient states a
geometrically decaying number of times: `I + Q + Q² + … = (I − Q)⁻¹ = N`.
`N[i][j]` = expected number of visits to transient `j` starting from `i`.
→ *expected agent attempts, runner-minutes.*

**Absorption probabilities.** To end in absorbing state `k`, the run must pass
through some transient `j` and then jump: `B = N·R`, `B[i][k]` = P(end in `k` | start `i`).
Every row of `B` sums to 1 — the run goes *somewhere* terminal, always.
→ *outcome percentages.*

**Steps to absorption.** `t = N·1` — expected hops summed over all transient visits.
→ *wall-clock forecast.*

**Expected cost.** With a per-state cost vector `c` (tokens, runner-seconds, or
unit weights): `C = N·c`.
→ *the budget number.*

## 3. Step augmentation keeps the math honest

Success probability decays per attempt, and attempt history matters. Decaying a
probability table per retry (the common industry hack) makes the chain
*history-dependent (non-Markov on the base state space)* — and silently breaks
`N = (I−Q)⁻¹`.

markov-ci instead expands loop-capable states into attempt-indexed states
(`s2#1 … s2#max_attempts`, `s3#1 …`) whose per-attempt edges come from the priors
(ADR-0002). The chain on the augmented space is genuinely Markov — all four results
above stay *exact*. Cost: a handful of extra states, bounded by `max_attempts = 3`.

## 4. Absorption by construction

If a loop-back edge carried probability ~1 with no exit, `I − Q` would be singular and
`N` would not exist — the runaway-loop incident, expressed as linear algebra.

markov-ci removes this failure mode structurally: at `max_attempts`, loop-back edges
are deleted and their probability mass re-normalizes into `a2`/`a3` (ADR-0004). Every
matrix the engine can execute is therefore absorbing — *no matter what the priors
say*. The model is acyclic after the cap (`Q` nilpotent); the runtime stops via its
attempt counter and per-call timeouts, with budgets the second, independent stop.

## 5. Worked example (the golden numbers)

Default structural edges: `s2→s3 = 0.95`, `s3→s4 = 0.65`, `s4→a1 = 0.90`,
`s3→s2 = 0.25` loop-back. The s2/s3 block:

```
Q_sub = ⎡ 0    0.95 ⎤      I − Q_sub = ⎡ 1    −0.95 ⎤     det = 1 − 0.2375 = 0.7625
        ⎣ 0.25 0    ⎦                  ⎣ −0.25  1   ⎦

N_sub = (1/0.7625) · ⎡ 1    0.95 ⎤ = ⎡ 1.312  1.246 ⎤
                     ⎣ 0.25 1    ⎦   ⎣ 0.328  1.312 ⎦
```

A run starting at `s2` visits `s2` ~1.31 times and `s3` ~1.25 times on average — the
"agent often needs a second pass" of field experience, now a computed expectation.

**P(a1 | s2):** succeed directly via `s2→s3→s4→a1 = 0.95·0.65·0.90 = 0.55575`, or loop
and retry (each loop multiplies by `0.95·0.25 = 0.2375`):

```
P(a1|s2) = 0.55575 / (1 − 0.2375) = 0.55575 / 0.7625 ≈ 0.729
```

**P(a1 | s0):** pass outright (0.82) or fail → triage → agent:

```
P(a1|s0) = 0.82 + 0.18 · 0.75 · 0.729 ≈ 0.918
```

Those are the **uncapped** values. Because the shipped default caps at
`max_attempts: 3`, the assembled chain gives P(a1 | s2) ≈ **0.72**, P(a1 | s1) ≈ **0.54**
and P(a1 | s0) ≈ **0.92**; as the attempt cap grows the first converges to 0.729. These —
`0.54`, `0.72`, `0.92` — are the golden values asserted across the test suite, docs, and
tutorials. `s1` (failed builds) is the default start state: the engine only runs after a
failure (M13.26).
Per-category priors (spec 0001 §4) modulate the `s2→s3` edge; the method is identical.

## 6. Uncertainty: Dirichlet posteriors

A matrix estimated from telemetry is a sample, not a truth. With transition counts
`n_ij` and a prior concentration `α`:

```
P̂[i][j] = (α_j + n_ij) / (α_0 + Σ_j n_ij)        (posterior mean)
```

markov-ci reports credible intervals alongside every empirical estimate
(`posterior(counts, prior, alpha)`). Cold start = **illustrative** priors clearly labeled
`source: prior`; drift beyond the interval is a *feature* — the system announces when
reality has moved.

## 7. What this model does not claim

- It does not make agents smarter — it makes their behavior measurable and bounded.
- Memorylessness is an approximation, handled explicitly by augmentation (§3), not by
  hope.
- Probabilities are only as good as telemetry; everything is labeled and intervalled.
