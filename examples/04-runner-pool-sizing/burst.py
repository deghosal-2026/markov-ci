"""Example 04 — the burst reality check (docs/spec/0009-queueing.md §2–3).

Erlang-C assumes Poisson arrivals; agent loops fan out. This report sizes the
agent pool with the closed form, then replays the same load through the
discrete-event simulator twice — once Poisson, once with a 20-loop burst at
2 PM — and prints the p95 divergence. The divergence *is the finding*.

Run: ``python examples/04-runner-pool-sizing/burst.py``
"""

from __future__ import annotations

from markov_ci.queueing import (
    burst_arrivals,
    erlang_c,
    exponential_services,
    poisson_arrivals,
    simulate,
)

LAM = 48.0  # agent-pool arrival rate (jobs/hour): 0.4 * 120
MU = 30.0  # per-runner service rate (jobs/hour)
C = 2  # agent runners (0.4 * 5)
DURATION = 24.0  # one day
BURST_COUNT = 200
BURST_AT = 14.0  # 2 PM
BURST_SPREAD = 1.0 / 60.0  # within a minute
SEED_ARRIVALS = 7
SEED_SERVICES = 99  # independent of arrivals — a shared seed suppresses waits


def _minutes(hours: float) -> float:
    return hours * 60.0


def main() -> None:
    closed = erlang_c(lam=LAM, mu=MU, c=C)

    poisson_times = poisson_arrivals(lam=LAM, duration=DURATION, seed=SEED_ARRIVALS)
    poisson = simulate(
        poisson_times,
        exponential_services(mu=MU, n=len(poisson_times), seed=SEED_SERVICES),
        c=C,
    )

    background = poisson_arrivals(
        lam=LAM - BURST_COUNT / DURATION, duration=DURATION, seed=SEED_ARRIVALS,
    )
    burst_times = burst_arrivals(
        count=BURST_COUNT, at=BURST_AT, spread=BURST_SPREAD, seed=SEED_ARRIVALS,
    )
    burst = simulate(
        sorted(background + burst_times),
        exponential_services(mu=MU, n=len(background) + BURST_COUNT, seed=SEED_SERVICES),
        c=C,
    )

    print(f"Agent pool — lambda={LAM:.0f}/h  mu={MU:.0f}/h  c={C}  rho={closed.rho:.3f}")
    print()
    print(f"{'model':<28}{'p50 (min)':>12}{'p95 (min)':>12}{'mean (min)':>12}")
    print(
        f"{'Erlang-C (closed form)':<28}"
        f"{'—':>12}{_minutes(closed.p95_wait):>12.2f}{_minutes(closed.mean_wait):>12.2f}",
    )
    print(
        f"{'DES — Poisson':<28}"
        f"{_minutes(poisson.p50_wait):>12.2f}{_minutes(poisson.p95_wait):>12.2f}"
        f"{_minutes(poisson.mean_wait):>12.2f}",
    )
    print(
        f"{f'DES — {BURST_COUNT}-loop burst @2 PM':<28}"
        f"{_minutes(burst.p50_wait):>12.2f}{_minutes(burst.p95_wait):>12.2f}"
        f"{_minutes(burst.mean_wait):>12.2f}",
    )
    print()
    ratio = burst.p95_wait / closed.p95_wait if closed.p95_wait else float("inf")
    print(
        f"burst p95 is {ratio:.1f}x the closed-form p95 — the burst, not the mean, "
        "sizes the pool.",
    )
    assert burst.p95_wait > closed.p95_wait, "burst must expose a worse tail than Erlang-C"


if __name__ == "__main__":
    main()
