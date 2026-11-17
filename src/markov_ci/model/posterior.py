"""Dirichlet posteriors and credible intervals (docs/spec/0002 §2).

A transition probability estimated from telemetry is a sample, not a truth.
Given per-target counts and a prior, this returns the posterior mean and a
credible interval per target, so empirical numbers are always shown with their
uncertainty — and cold start falls back to the labelled prior.

The interval uses the normal approximation to the marginal Beta distribution
(no SciPy dependency); it is clipped to ``[0, 1]``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Posterior:
    """Posterior mean and credible interval per target."""

    mean: tuple[float, ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (Acklam's rational approximation)."""
    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00)
    low, high = 0.02425, 1 - 0.02425
    if p < low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    if p > high:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
        ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
    )


def posterior(
    counts: Sequence[int],
    prior: Sequence[float],
    alpha: float = 1.0,
    level: float = 0.95,
) -> Posterior:
    """Dirichlet posterior mean and credible intervals per target.

    ``alpha`` scales the prior concentration (prior strength in pseudo-counts).
    """
    if not counts or not prior:
        raise ValueError("counts and prior must be non-empty")
    if len(counts) != len(prior):
        raise ValueError("counts and prior must have the same length")
    if any(count < 0 for count in counts):
        raise ValueError("counts must be non-negative")
    if any(p <= 0 for p in prior):
        raise ValueError("prior entries must be positive")

    total_prior = sum(prior)
    normalised_prior = [p / total_prior for p in prior]
    concentration = [alpha * p for p in normalised_prior]

    total_count = sum(counts)
    denominator = alpha + total_count

    means: list[float] = []
    lowers: list[float] = []
    uppers: list[float] = []
    z = _norm_ppf(1 - (1 - level) / 2)

    for concentration_j, count in zip(concentration, counts, strict=True):
        a = concentration_j + count
        b = denominator - a
        mean = a / denominator
        variance = (a * b) / (denominator * denominator * (denominator + 1))
        spread = z * math.sqrt(variance) if variance > 0 else 0.0
        means.append(mean)
        lowers.append(max(0.0, mean - spread))
        uppers.append(min(1.0, mean + spread))

    return Posterior(
        mean=tuple(means),
        lower=tuple(lowers),
        upper=tuple(uppers),
    )
