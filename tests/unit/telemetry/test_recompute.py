"""M8.2 (#38) — recompute empirical priors from telemetry (spec 0007 §4)."""

from __future__ import annotations

from typing import Any

import pytest

from markov_ci.telemetry.recompute import recompute


def _transition(
    *, adapter: str, category: str, attempt: int, fro: str, to: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event": "transition",
        "run_id": "run",
        "commit_sha": "abc",
        "pr_number": 1,
        "from_state": fro,
        "to_state": to,
        "duration_ms": 1,
        "tokens_used": 0,
        "failure_category": category,
        "attempt": attempt,
        "adapter": adapter,
        "ts": "2026-11-16T09:41:07Z",
    }


def _attempt(*, adapter: str, category: str, attempt: int, success: bool) -> list[dict[str, Any]]:
    events = [
        _transition(
            adapter=adapter, category=category, attempt=attempt,
            fro=f"s2_agent_reasoning#{attempt}", to=f"s3_sandbox_validation#{attempt}",
        ),
    ]
    if success:
        events.append(
            _transition(
                adapter=adapter, category=category, attempt=attempt,
                fro=f"s3_sandbox_validation#{attempt}", to="s4_regression_check",
            ),
        )
    return events


def test_empty_events_yield_empty_priors() -> None:
    assert recompute([]) == {}


def test_success_rate_is_derived_from_transitions() -> None:
    events: list[dict[str, Any]] = []
    for _ in range(8):
        events += _attempt(adapter="simulated", category="unit_assertion", attempt=1, success=True)
    for _ in range(2):
        events += _attempt(adapter="simulated", category="unit_assertion", attempt=1, success=False)

    priors = recompute(events, alpha=0.0)
    assert priors["simulated"]["unit_assertion"]["success"][0] == pytest.approx(0.8)


def test_result_is_labelled_empirical() -> None:
    events = _attempt(adapter="simulated", category="lint_error", attempt=1, success=True)
    priors = recompute(events)
    assert priors["simulated"]["lint_error"]["source"] == "empirical"


def test_per_adapter_and_category_are_separated() -> None:
    events = (
        _attempt(adapter="simulated", category="lint_error", attempt=1, success=True)
        + _attempt(adapter="claude-code", category="lint_error", attempt=1, success=False)
    )
    priors = recompute(events, alpha=0.0)
    assert set(priors) == {"simulated", "claude-code"}
    assert priors["simulated"]["lint_error"]["success"][0] == 1.0
    assert priors["claude-code"]["lint_error"]["success"][0] == 0.0


def test_prior_smoothing_applies() -> None:
    events = _attempt(adapter="simulated", category="lint_error", attempt=1, success=True)
    prior = {"simulated": {"lint_error": [0.5, 0.5, 0.5]}}
    priors = recompute(events, alpha=2.0, prior=prior)
    # (2*0.5 + 1) / (2 + 1) = 0.666...
    assert priors["simulated"]["lint_error"]["success"][0] == pytest.approx(2 / 3)


def test_multi_attempt_curve_is_reconstructed() -> None:
    events = (
        _attempt(adapter="s", category="unit_assertion", attempt=1, success=False)
        + _attempt(adapter="s", category="unit_assertion", attempt=2, success=True)
    )
    priors = recompute(events, alpha=0.0)
    assert priors["s"]["unit_assertion"]["success"][1] == pytest.approx(1.0)


def test_output_merges_into_a_config() -> None:
    from markov_ci.config import chain_from_config, parse_config
    from markov_ci.data import default_config_path

    events = _attempt(adapter="simulated", category="lint_error", attempt=1, success=True)
    priors = recompute(events)
    merged = parse_config(default_config_path().read_text(encoding="utf-8"))
    merged_priors = dict(merged.priors)
    merged_priors["evolved"] = {
        "lint_error": type(merged_priors["default"]["lint_error"])(
            success=priors["simulated"]["lint_error"]["success"],
            cost_weight=1.0,
            source="empirical",
        ),
    }
    updated = merged.model_copy(update={"priors": merged_priors})
    chain = chain_from_config(updated, category="lint_error", adapter="evolved")
    assert chain.transient
