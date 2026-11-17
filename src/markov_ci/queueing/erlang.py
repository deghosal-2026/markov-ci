"""Erlang-C for the M/M/c runner model (docs/spec/0009-queueing.md §1).

``lam`` is the arrival rate and ``mu`` the per-server service rate, in the same
time unit; waits are returned in that unit (e.g. per-hour rates give hour waits).

Reference (docs/explanations/queueing-theory.md §2): ``c=5, lam=120, mu=30`` gives
``rho = 0.8``, ``P_wait ≈ 0.554``, mean wait ≈ 0.0185, p95 ≈ 0.080.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueMetrics:
    """The M/M/c performance measures for a runner pool."""

    rho: float
    p_wait: float
    mean_wait: float
    p95_wait: float
    offered_load: float
    utilisation: float


def _erlang_c(offered_load: float, c: int) -> float:
    """Probability that an arriving job must wait (Erlang-C)."""
    a = offered_load
    if a == 0.0:
        return 0.0
    # sum_{k=0}^{c-1} a^k / k!  (built iteratively to avoid overflow)
    term = 1.0
    series = 1.0
    for k in range(1, c):
        term *= a / k
        series += term
    term_c = math.exp(c * math.log(a) - math.lgamma(c + 1))
    tail = term_c * (c / (c - a))
    return tail / (series + tail)


def erlang_c(
    *,
    lam: float,
    mu: float,
    c: int,
    level: float = 0.95,
) -> QueueMetrics:
    """Return the M/M/c metrics for arrival rate ``lam`` and service rate ``mu``."""
    if lam < 0:
        raise ValueError("lam must be non-negative")
    if mu <= 0:
        raise ValueError("mu must be positive")
    if c < 1:
        raise ValueError("c must be >= 1")
    if lam >= c * mu:
        raise ValueError(
            "system is not stable: lam must be smaller than c*mu "
            f"(got lam={lam}, c*mu={c * mu})",
        )

    offered_load = lam / mu
    rho = offered_load / c
    p_wait = _erlang_c(offered_load, c)
    drain_rate = c * mu - lam
    mean_wait = p_wait / drain_rate
    # when P_wait <= 1-level, fewer than `level` of arrivals wait at all → p95 = 0
    p95_wait = (
        0.0 if p_wait <= (1.0 - level)
        else math.log(p_wait / (1.0 - level)) / drain_rate
    )

    return QueueMetrics(
        rho=rho,
        p_wait=p_wait,
        mean_wait=mean_wait,
        p95_wait=p95_wait,
        offered_load=offered_load,
        utilisation=rho,
    )
