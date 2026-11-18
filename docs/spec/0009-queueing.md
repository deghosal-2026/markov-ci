# Spec 0009 — Queueing (runner fleets)

**Status:** Experimental until v0.2 · **Implements:** PRD F16

Agentic repair loops change the *shape* of CI load: humans push in diurnal waves; agents
fire bursty, recursive validation runs. This module sizes runner pools for both.

## 1. Erlang-C (M/M/c) — `erlang_c(lam, mu, c) -> QueueMetrics`

- `rho = lam / (c * mu)` — utilization; requires `lam < c * mu` (else: clear error,
  never a bogus number).
- `P_wait` — Erlang-C formula; probability a job waits at all.
- `Wq` — mean wait `= P_wait / (c*mu − lam)`.
- `p95_wait` — exact for M/M/c: `t = ln(P_wait / 0.05) / (c*mu − lam)`.
- Service level: P(wait ≤ t) for user-supplied t.

## 2. Discrete-event simulator — `simulate(...) -> SimReport`

M/M/c assumes Poisson arrivals and exponential service — both are lies for agentic
traffic. The DES accepts arbitrary arrival patterns (e.g., bursty agent fan-out:
20 simultaneous agent loops at 2 PM) and empirical service-time distributions, and
reports wait percentiles (p50/p95/p99) and utilization per pool.

## 3. Monte-Carlo vs closed form — a check, not validation

Under Poisson input, DES output must converge to Erlang-C within tolerance (property
test). That agreement is a **Monte-Carlo vs linear-algebra / closed-form consistency
check**: it corroborates that the two implementations agree with each other. It is **not**
"validation" of the model, and it says nothing about whether M/M/c's assumptions match
real agentic traffic. Under bursty input the divergence *is the finding* —
explanations/queueing-theory.md explains when the closed form is good enough.

## 4. Partitioning guidance (productized in `queue` output)

- Human-initiated builds: high-priority warm pool — protect flow state; target
  p95 wait < 60 s.
- Agent loop iterations: lower-priority spot/burst pool — cheap, interruptible,
  budget-capped by spec 0004 anyway.
- The `queue` command prints both pools' numbers side-by-side for the requested
  lambda split.
