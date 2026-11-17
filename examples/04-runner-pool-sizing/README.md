# Example 04 — runner-pool sizing

**Ships:** v0.2.0 (F16, F18) · **Exit code to expect:** `0` · **Tutorial:** [04 — runner pools](../../docs/tutorials/04-runner-pool-sizing.md)

Size a runner fleet for two populations that behave nothing alike: humans push in
diurnal waves, agent loops fan out in bursts. Erlang-C gives the quick estimate; the
discrete-event simulator shows what the burst does to the tail.

## Run it

```bash
markov-ci queue --lambda 120 --mu 30 --c 5 --simulate --json
echo $?    # 0
```

## Expected output

```
markov-ci queue — mu=30.0 · c=5 · human_share=0.6

[human] c=3 lambda=72.0 rho=0.800
    p_wait=0.647 mean_wait=0.0360 p95_wait=0.1423
[agent] c=2 lambda=48.0 rho=0.800
    p_wait=0.711 mean_wait=0.0593 p95_wait=0.2212
```

Both pools sit at `ρ = 0.8`. The `--simulate` flag adds a discrete-event run beside the
closed form; `--json` feeds a capacity dashboard directly.

## The burst reality check

```bash
python examples/04-runner-pool-sizing/burst.py
```

```
Agent pool — lambda=48/h  mu=30/h  c=2  rho=0.800

model                          p50 (min)   p95 (min)  mean (min)
Erlang-C (closed form)                 —       13.27        3.56
DES — Poisson                       1.57       11.10        3.00
DES — 200-loop burst @2 PM           8.24      206.75       58.55

burst p95 is 15.6x the closed-form p95 — the burst, not the mean, sizes the pool.
```

## What this proves

**Poisson is a polite fiction for agent traffic.** Under Poisson input the simulator
converges to the closed form (11.1 vs 13.3 min p95); under a realistic 2 PM fan-out the
same *total* load blows p95 out to **206 minutes** — 15.6× the closed form. The mean
(58.6 min) barely moves the story; the *tail* is what a developer feels. That is why the
product answer is two pools: humans on a warm, protected pool (p95 < 60 s target), agent
iterations on a cheap, interruptible burst pool whose worst case is bounded by the policy
budgets anyway (spec 0004, CUJ-3).

## Forecast vs. actual

| Quantity | Forecast | This report |
|---|---|---|
| Erlang-C p95 (agent pool) | 13.27 min | DES-Poisson 11.10 min (converges) |
| Burst p95 (200 loops @2 PM) | not modeled by Erlang-C | **206.75 min** (15.6× the closed form) |
| pool utilisation | ρ = 0.800 | 0.800 (both pools) |

`λ ≥ cμ` is refused with guidance, never answered with a bogus number — the closed form
never lies about instability. The queue module is standalone: it sizes *any* fleet, no
`markov-ci run` required.
