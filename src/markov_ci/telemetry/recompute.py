"""Recompute empirical priors from telemetry (docs/spec/0007-telemetry-events.md §4).

The event stream alone is enough to rebuild the model. For each
``(adapter, category)`` we estimate the per-attempt success probability of a patch
as ``P(s4 reached | s2#k entered)``, smoothed toward any supplied prior with a
Dirichlet-style pseudo-count ``alpha``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from markov_ci.model.posterior import posterior


def _key(event: Mapping[str, Any]) -> tuple[str, str]:
    return str(event.get("adapter", "simulated")), str(event.get("failure_category", "unknown"))


def _attempt_of(state: str) -> int:
    if "#" in state:
        _, _, suffix = state.partition("#")
        if suffix.isdigit():
            return int(suffix)
    return 1


def recompute(
    events: Sequence[Mapping[str, Any]],
    *,
    alpha: float = 1.0,
    prior: Mapping[str, Mapping[str, Sequence[float]]] | None = None,
    min_attempts: int = 3,
    include_synthetic: bool = False,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Rebuild empirical priors, keyed by adapter then category.

    Simulated (``synthetic``) events are excluded by default so the priors reflect
    real runs, not the offline demo (M13.29). Curves are padded to at least
    ``min_attempts`` so the output can be dropped straight into a config whose
    ``max_attempts`` is that value.
    """
    attempted: dict[tuple[str, str], dict[int, int]] = {}
    succeeded: dict[tuple[str, str], dict[int, int]] = {}

    for event in events:
        if event.get("event", "transition") not in {"transition", "gate_rejected"}:
            continue
        if event.get("synthetic") and not include_synthetic:
            continue
        key = _key(event)
        fro = str(event.get("from_state", ""))
        to = str(event.get("to_state", ""))
        if fro.startswith("s2_agent_reasoning"):
            attempt = _attempt_of(fro)
            attempted.setdefault(key, {}).setdefault(attempt, 0)
            attempted[key][attempt] += 1
        elif fro.startswith("s3_sandbox_validation") and to.startswith("s4_regression_check"):
            attempt = _attempt_of(fro)
            succeeded.setdefault(key, {}).setdefault(attempt, 0)
            succeeded[key][attempt] += 1

    result: dict[str, dict[str, dict[str, Any]]] = {}
    for (adapter, category), attempts in attempted.items():
        max_attempt = max(max(attempts), min_attempts)
        success_counts = succeeded.get((adapter, category), {})
        curve: list[float] = []
        for attempt in range(1, max_attempt + 1):
            trials = attempts.get(attempt, 0)
            wins = success_counts.get(attempt, 0)
            prior_values = _prior_curve(prior, adapter, category, attempt, max_attempt)
            if trials == 0:
                curve.append(prior_values[attempt - 1])
                continue
            smoothed = posterior(
                counts=(wins, trials - wins),
                prior=(prior_values[attempt - 1], 1.0 - prior_values[attempt - 1]),
                alpha=alpha,
            )
            curve.append(smoothed.mean[0])
        result.setdefault(adapter, {})[category] = {
            "success": curve,
            "source": "empirical",
        }
    return result


def _prior_curve(
    prior: Mapping[str, Mapping[str, Sequence[float]]] | None,
    adapter: str,
    category: str,
    attempt: int,
    max_attempt: int,
) -> list[float]:
    if prior is not None:
        block = prior.get(adapter) or prior.get("default")
        if block is not None:
            values = block.get(category)
            if values is not None and len(values) >= attempt:
                return list(values)
    return [0.5] * max_attempt
