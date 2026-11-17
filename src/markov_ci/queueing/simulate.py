"""Discrete-event runner simulator (docs/spec/0009-queueing.md §2).

M/M/c assumes Poisson arrivals and exponential service — both are lies for agentic
traffic, which fans out in bursts. This simulator takes arbitrary arrival times and
empirical service durations, so bursty reality can be compared against the closed
form.
"""

from __future__ import annotations

import heapq
import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimReport:
    """Wait percentiles and utilisation from a simulation."""

    p50_wait: float
    p95_wait: float
    p99_wait: float
    mean_wait: float
    p_wait: float
    utilisation: float
    served: int


def _percentile(ordered: Sequence[float], quantile: float) -> float:
    if not ordered:
        return 0.0
    index = round(quantile * (len(ordered) - 1))
    return ordered[min(max(index, 0), len(ordered) - 1)]


def simulate(arrivals: Sequence[float], services: Sequence[float], c: int) -> SimReport:
    """Simulate a work-conserving FIFO queue with ``c`` servers."""
    if c < 1:
        raise ValueError("c must be >= 1")
    if len(arrivals) != len(services):
        raise ValueError("arrivals and services must have the same length")
    if not arrivals:
        return SimReport(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    order = sorted(range(len(arrivals)), key=lambda i: arrivals[i])
    free: list[float] = [0.0] * c
    heapq.heapify(free)
    waits: list[float] = []
    busy = 0.0
    first = arrivals[order[0]]
    last = first

    for i in order:
        arrival = arrivals[i]
        duration = services[i]
        available = heapq.heappop(free)
        start = max(arrival, available)
        waits.append(start - arrival)
        end = start + duration
        busy += duration
        heapq.heappush(free, end)
        last = max(last, end)

    makespan = last - first if last > first else 1.0
    ordered = sorted(waits)
    waited = sum(1 for wait in waits if wait > 0) / len(waits)
    return SimReport(
        p50_wait=_percentile(ordered, 0.50),
        p95_wait=_percentile(ordered, 0.95),
        p99_wait=_percentile(ordered, 0.99),
        mean_wait=sum(waits) / len(waits),
        p_wait=waited,
        utilisation=busy / (c * makespan),
        served=len(waits),
    )


def poisson_arrivals(lam: float, duration: float, seed: int = 0) -> list[float]:
    """Poisson arrival times with rate ``lam`` over ``[0, duration)``."""
    rng = random.Random(seed)
    times: list[float] = []
    current = 0.0
    while True:
        current += rng.expovariate(lam)
        if current >= duration:
            break
        times.append(current)
    return times


def exponential_services(mu: float, n: int, seed: int = 0) -> list[float]:
    """``n`` exponential service durations with rate ``mu``."""
    rng = random.Random(seed)
    return [rng.expovariate(mu) for _ in range(n)]


def burst_arrivals(count: int, *, at: float, spread: float, seed: int = 0) -> list[float]:
    """``count`` arrivals clustered in ``[at, at + spread)`` — an agent fan-out."""
    rng = random.Random(seed)
    return [at + rng.uniform(0.0, spread) for _ in range(count)]
