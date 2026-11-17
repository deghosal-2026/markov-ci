"""M7.1 (#34) — Erlang-C for M/M/c (docs/spec/0009-queueing.md §1)."""

from __future__ import annotations

import math

import pytest

from markov_ci.queueing.erlang import QueueMetrics, erlang_c


def test_worked_example_from_the_docs() -> None:
    # c=5 runners, lambda=120 jobs/h, mu=30 jobs/h  (docs/explanations/queueing-theory.md §2)
    metrics = erlang_c(lam=120, mu=30, c=5)
    assert isinstance(metrics, QueueMetrics)
    assert metrics.rho == pytest.approx(0.8, abs=1e-9)
    assert metrics.p_wait == pytest.approx(0.554, abs=0.005)
    assert metrics.mean_wait == pytest.approx(0.01847, abs=0.001)  # hours
    assert metrics.p95_wait == pytest.approx(0.0802, abs=0.002)  # hours


def test_p95_is_larger_than_the_mean_wait() -> None:
    metrics = erlang_c(lam=120, mu=30, c=5)
    assert metrics.p95_wait > metrics.mean_wait


def test_offered_load_is_lambda_over_mu() -> None:
    assert erlang_c(lam=120, mu=30, c=5).offered_load == pytest.approx(4.0)


def test_low_utilisation_has_little_waiting() -> None:
    metrics = erlang_c(lam=10, mu=30, c=5)
    assert metrics.rho < 0.1
    assert metrics.p_wait < 0.01
    # fewer than 95% wait → the 95th-percentile wait is zero, never negative
    assert metrics.p95_wait == 0.0


def test_single_server() -> None:
    metrics = erlang_c(lam=5, mu=10, c=1)
    assert metrics.rho == pytest.approx(0.5)
    assert 0.0 <= metrics.p_wait <= 1.0


def test_unstable_system_is_rejected() -> None:
    with pytest.raises(ValueError, match="stable"):
        erlang_c(lam=200, mu=30, c=5)


def test_exactly_saturated_is_rejected() -> None:
    with pytest.raises(ValueError):
        erlang_c(lam=150, mu=30, c=5)


@pytest.mark.parametrize(
    ("lam", "mu", "c"),
    [(120, 0, 5), (120, 30, 0), (120, 30, -1), (-1, 30, 5)],
)
def test_invalid_inputs_are_rejected(lam: float, mu: float, c: int) -> None:
    with pytest.raises(ValueError):
        erlang_c(lam=lam, mu=mu, c=c)


def test_rho_never_reaches_one_for_a_stable_system() -> None:
    metrics = erlang_c(lam=149.9, mu=30, c=5)
    assert 0.0 <= metrics.rho < 1.0


def test_larger_fleet_reduces_wait() -> None:
    small = erlang_c(lam=120, mu=30, c=5)
    large = erlang_c(lam=120, mu=30, c=8)
    assert large.mean_wait < small.mean_wait


def test_deterministic() -> None:
    assert erlang_c(lam=120, mu=30, c=5) == erlang_c(lam=120, mu=30, c=5)


def test_large_server_count_is_numerically_stable() -> None:
    metrics = erlang_c(lam=500, mu=30, c=40)
    assert math.isfinite(metrics.p_wait)
    assert 0.0 <= metrics.p_wait <= 1.0
