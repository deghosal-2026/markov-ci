# Tutorial 04 — Runner pool sizing

**Demo:** `examples/04-runner-pool-sizing` · **Ships:** v0.2.0 (F16, F18)

The developer-experience story: twenty agents enter repair loops at 2 PM — does anyone
human notice? Size two pools, route by who's asking, and keep p95 wait under a minute.

## Quick estimate — Erlang-C

```bash
markov-ci queue --lambda 120 --mu 30 --c 5          # jobs/hour
```

Prints utilization `ρ`, `P_wait`, mean wait `Wq`, and exact p95 for **both** pools — the
human/agent split (`--human-share`, default 0.6) — plus the discrete-event run with
`--simulate` (spec 0009). With `λ=120, μ=30, c=5` each pool sits at `ρ = 0.8`; the
single-pool worked example (`P_wait ≈ 0.55`, `Wq ≈ 1.1 min`, `p95 ≈ 4.8 min`) is in
[queueing theory](../explanations/queueing-theory.md).

Ask the inverse too — *how many warm runners for p95 < 60 s at this load?* — by
sweeping `--c` until the target holds.

## The burst reality check

Poisson arrivals are a polite fiction for agentic traffic; agents fan out. The
discrete-event simulator takes the burst pattern instead — the demo drives it directly:

```bash
python3 examples/04-runner-pool-sizing/burst.py
```

Under Poisson input the DES converges to Erlang-C (11.1 vs 13.3 min p95, property-tested);
under a 2 PM fan-out of 200 agent loops **the divergence is the finding** — p95 blows out
to ~207 min, 15.6× the closed form, while the mean barely moves.

## Partition the fleet (the product answer)

| Pool | Serves | Sizing tool | Target |
|---|---|---|---|
| Warm, high priority | human-initiated builds | Erlang-C on human-only λ | p95 wait < 60 s |
| Burst, low priority | agent loop iterations | DES on the burst pattern | cheap + interruptible; policy budgets bound the worst case anyway |

Route agent iterations to the burst pool in your runner labels/groups; humans keep the
warm pool. Agent saturation then degrades *agent* latency, not developer flow (CUJ-3).

## What to notice

- The queue module is standalone — it works on any fleet, no markov-ci `run` needed.
- `--json` output feeds your capacity dashboards directly.
- λ ≥ cμ is refused with guidance, never answered with a bogus number.
