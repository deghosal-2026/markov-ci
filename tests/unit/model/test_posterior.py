"""M1.6 (#12) — Dirichlet posteriors + credible intervals (spec 0002 §2)."""

from __future__ import annotations

import pytest

from markov_ci.model.posterior import Posterior, posterior

UNIFORM = (0.5, 0.5)


def test_zero_counts_returns_the_prior() -> None:
    result = posterior((0, 0), UNIFORM)
    assert result.mean == pytest.approx((0.5, 0.5), abs=1e-12)


def test_mean_converges_to_the_empirical_rate() -> None:
    result = posterior((900, 100), UNIFORM, alpha=1.0)
    assert result.mean[0] == pytest.approx(0.9, abs=0.01)
    assert result.mean[1] == pytest.approx(0.1, abs=0.01)


def test_means_sum_to_one() -> None:
    result = posterior((10, 5, 1), (0.5, 0.3, 0.2))
    assert sum(result.mean) == pytest.approx(1.0, abs=1e-12)


def test_interval_contains_the_mean() -> None:
    result = posterior((7, 3), UNIFORM)
    for mean, lower, upper in zip(result.mean, result.lower, result.upper, strict=True):
        assert lower <= mean <= upper


def test_intervals_are_within_the_unit_interval() -> None:
    result = posterior((0, 0), UNIFORM)
    assert all(0.0 <= value <= 1.0 for value in (*result.lower, *result.upper))


def test_more_evidence_shrinks_the_interval() -> None:
    few = posterior((5, 5), UNIFORM)
    many = posterior((5000, 5000), UNIFORM)
    few_width = few.upper[0] - few.lower[0]
    many_width = many.upper[0] - many.lower[0]
    assert many_width < few_width


def test_higher_level_widens_the_interval() -> None:
    narrow = posterior((20, 20), UNIFORM, level=0.80)
    wide = posterior((20, 20), UNIFORM, level=0.99)
    assert (wide.upper[0] - wide.lower[0]) > (narrow.upper[0] - narrow.lower[0])


def test_deterministic() -> None:
    assert posterior((3, 4), UNIFORM) == posterior((3, 4), UNIFORM)


def test_length_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="same length"):
        posterior((1, 2), (0.5,))


def test_negative_counts_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        posterior((-1, 2), UNIFORM)


def test_prior_must_be_positive() -> None:
    with pytest.raises(ValueError, match="prior"):
        posterior((1, 2), (0.0, 1.0))


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        posterior((), ())


def test_result_is_frozen() -> None:
    result = posterior((1, 1), UNIFORM)
    assert isinstance(result, Posterior)
    assert isinstance(result.mean, tuple)
