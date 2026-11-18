# Queueing theory for runner fleets

Agentic repair changes the *shape* of CI load: humans push in diurnal waves; agents
fire bursty, recursive validation runs. Queue wait is the silent killer of developer flow —
this is the math for keeping it bounded.

## 1. The M/M/c model

Model the runner pool as `c` servers. Jobs arrive at rate **λ** (Poisson), each runner
completes work at rate **μ** (exponential). Offered load in erlangs: `a = λ/μ`;
utilization: `ρ = a/c`. Stability requires `ρ < 1` — markov-ci refuses to compute a
queue that cannot clear (spec 0009).

**Erlang-C** — the probability an arriving job must wait at all:

```
P_wait = [ (a^c / c!) · c/(c − a) ] / [ Σ_{k=0}^{c−1} a^k/k!  +  (a^c / c!) · c/(c − a) ]
       = [ a^c / (c! · (1 − ρ)) ]     / [ Σ_{k=0}^{c−1} a^k/k!  +  a^c / (c! · (1 − ρ)) ]
```

(The numerator and denominator both carry the factor `c/(c − a) = 1/(1 − ρ)`, as the
worked example below applies.)

**Mean wait:** `Wq = P_wait / (cμ − λ)`
**p95 wait** (exact for M/M/c — a job either doesn't wait, or waits exponentially):

```
P(W > t) = P_wait · e^−(cμ−λ)t   →   p95 = ln(P_wait / 0.05) / (cμ − λ)
```

## 2. Worked example

Fleet: `c = 5` warm runners, arrivals `λ = 120` jobs/hour (2 PM burst), service
`μ = 30` jobs/hour per runner. Then `a = 4`, `ρ = 0.8`:

```
Σ_{k=0}^{4} 4^k/k! = 1 + 4 + 8 + 10.67 + 10.67 = 34.33
4^5/5! · 5/(5−4)   = 8.53 × 5 = 42.67
P_wait = 42.67 / (34.33 + 42.67) ≈ 0.554
Wq     = 0.554 / (150 − 120) ≈ 1.1 minutes
p95    = ln(0.554/0.05) / 30 ≈ 4.8 minutes
```

55% of jobs wait; the p95 developer loses ~5 minutes to the queue. Whether that is
acceptable is a product decision — now it's a *visible* one.

## 3. Where M/M/c lies for agentic traffic

Both M's are optimistic for agents:

- **Arrivals are not Poisson** — agent loops fan out in bursts (twenty simultaneous
  validation runs at 2 PM), not smooth randomness.
- **Service times are not exponential** — regression checks have a floor; agent loops
  have heavy tails.

The closed form is the quick estimator; the discrete-event simulator (spec 0009 §2)
takes arbitrary arrival patterns and empirical service distributions. Under Poisson
input the DES must converge to Erlang-C (property test); under bursty input, *the
divergence is the finding*. This agreement is a **Monte-Carlo vs closed-form
consistency check**, not validation of the model (spec 0009 §3).

## 4. Partitioning: the product answer

Split the fleet and route by who's asking (PRD F16, CUJ-3):

| Pool | Serves | Sized by | Target |
|---|---|---|---|
| Warm, high priority | Human-initiated builds | Erlang-C on human-only λ | p95 wait < 60 s |
| Burst, low priority | Agent loop iterations | DES on agent burst pattern | cheap, interruptible — and budget-capped anyway by the policy engine |

Agents saturating their own pool degrades agent latency, not developer flow — and the
policy's token/wall-clock budgets (spec 0004) bound the burst pool's worst case
independently of queueing.

`markov-ci queue --lambda L --mu M --c N` prints both pools side-by-side;
`--simulate` runs the burst DES.
