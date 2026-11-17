"""M7.2 (#35) — discrete-event runner simulator (docs/spec/0009-queueing.md §2)."""

from __future__ import annotations

import pytest

from markov_ci.queueing.erlang import erlang_c
from markov_ci.queueing.simulate import (
    SimReport,
    burst_arrivals,
    exponential_services,
    poisson_arrivals,
    simulate,
)


def test_report_shape() -> None:
    arrivals = poisson_arrivals(lam=120, duration=50, seed=1)
    services = exponential_services(mu=30, n=len(arrivals), seed=2)
    report = simulate(arrivals, services, c=5)
    assert isinstance(report, SimReport)
    assert report.served == len(arrivals)


def test_percentiles_are_ordered() -> None:
    arrivals = poisson_arrivals(lam=120, duration=100, seed=2)
    services = exponential_services(mu=30, n=len(arrivals), seed=3)
    report = simulate(arrivals, services, c=5)
    assert report.p50_wait <= report.p95_wait <= report.p99_wait


def test_is_deterministic() -> None:
    arrivals = poisson_arrivals(lam=120, duration=100, seed=3)
    services = exponential_services(mu=30, n=len(arrivals), seed=3)
    assert simulate(arrivals, services, c=5) == simulate(arrivals, services, c=5)


def test_converges_to_erlang_c_under_poisson_input() -> None:
    # NOTE: arrivals and services must use *independent* seeds — reusing one seed
    # ties the two exponential streams together and suppresses waits.
    lam, mu, c = 120.0, 30.0, 5
    arrivals = poisson_arrivals(lam=lam, duration=2000, seed=7)
    services = exponential_services(mu=mu, n=len(arrivals), seed=99)
    report = simulate(arrivals, services, c=c)
    analytic = erlang_c(lam=lam, mu=mu, c=c)
    # the fraction that wait matches Erlang-C's P_wait
    assert report.p_wait == pytest.approx(analytic.p_wait, abs=0.03)
    # the mean wait matches the closed form
    assert report.mean_wait == pytest.approx(analytic.mean_wait, rel=0.20)
    assert report.utilisation == pytest.approx(analytic.rho, abs=0.05)


def test_burst_traffic_diverges_from_poisson() -> None:
    c = 5
    smooth = poisson_arrivals(lam=120, duration=200, seed=11)
    smooth_services = exponential_services(mu=30, n=len(smooth), seed=21)
    smooth_report = simulate(smooth, smooth_services, c=c)

    bursty = burst_arrivals(count=len(smooth), at=0.0, spread=5.0, seed=31)
    burst_services = exponential_services(mu=30, n=len(bursty), seed=41)
    burst_report = simulate(bursty, burst_services, c=c)

    assert burst_report.p95_wait > smooth_report.p95_wait


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        simulate([1.0, 2.0], [1.0], c=2)
    with pytest.raises(ValueError):
        simulate([1.0], [1.0], c=0)


def test_empty_arrivals() -> None:
    report = simulate([], [], c=3)
    assert report.served == 0
    assert report.mean_wait == 0.0
