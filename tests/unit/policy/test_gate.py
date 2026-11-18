"""M2.1 (#15) — Policy and the ordered gate (docs/spec/0004-policy-engine.md)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from markov_ci.policy import A2, A3, Decision, GateResult, Policy, evaluate


def _eval(
    policy: Policy | None = None,
    *,
    attempt: int = 1,
    tokens_used: int = 0,
    elapsed_seconds: float = 0.0,
    next_success_probability: float = 0.9,
) -> GateResult:
    return evaluate(
        policy or Policy(),
        attempt=attempt,
        tokens_used=tokens_used,
        elapsed_seconds=elapsed_seconds,
        next_success_probability=next_success_probability,
    )


def test_defaults_match_the_spec() -> None:
    policy = Policy()
    assert policy.min_confidence == 0.40
    assert policy.max_attempts == 3
    assert policy.max_tokens == 200_000
    assert policy.wall_clock_seconds == 900


def test_invalid_policy_is_rejected() -> None:
    with pytest.raises(ValueError):
        Policy(min_confidence=1.5)
    with pytest.raises(ValueError):
        Policy(min_confidence=-0.1)
    with pytest.raises(ValueError):
        Policy(max_attempts=0)
    with pytest.raises(ValueError):
        Policy(max_tokens=0)
    with pytest.raises(ValueError):
        Policy(wall_clock_seconds=0)


def test_proceed_when_every_gate_passes() -> None:
    result = _eval()
    assert result.decision is Decision.PROCEED
    assert result.absorbing_state is None
    assert result.reason


def test_token_budget_trips_to_a3() -> None:
    result = _eval(tokens_used=200_001)
    assert result.decision is Decision.BUDGET_EXCEEDED
    assert result.absorbing_state == A3


def test_exact_token_budget_is_allowed() -> None:
    assert _eval(tokens_used=200_000).decision is Decision.PROCEED


def test_wall_clock_budget_trips_to_a3() -> None:
    result = _eval(elapsed_seconds=901.0)
    assert result.decision is Decision.BUDGET_EXCEEDED
    assert result.absorbing_state == A3


def test_attempt_cap_trips_to_a2() -> None:
    result = _eval(attempt=4)
    assert result.decision is Decision.ESCALATE
    assert result.absorbing_state == A2


def test_last_allowed_attempt_is_permitted() -> None:
    assert _eval(attempt=3).decision is Decision.PROCEED


def test_low_confidence_trips_to_a2() -> None:
    result = _eval(next_success_probability=0.15)
    assert result.decision is Decision.ESCALATE
    assert result.absorbing_state == A2


def test_confidence_exactly_at_threshold_is_permitted() -> None:
    assert _eval(next_success_probability=0.40).decision is Decision.PROCEED


def test_budget_outranks_confidence() -> None:
    result = _eval(tokens_used=10**9, next_success_probability=0.0)
    assert result.decision is Decision.BUDGET_EXCEEDED


def test_cap_outranks_confidence() -> None:
    result = _eval(attempt=9, next_success_probability=0.0)
    assert result.decision is Decision.ESCALATE
    assert result.absorbing_state == A2


def test_budget_outranks_the_cap() -> None:
    result = _eval(attempt=9, tokens_used=10**9)
    assert result.decision is Decision.BUDGET_EXCEEDED


def test_rejections_always_carry_a_reason() -> None:
    assert _eval(tokens_used=10**9).reason
    assert _eval(attempt=4).reason
    assert _eval(next_success_probability=0.0).reason


def test_gate_result_is_frozen() -> None:
    result = _eval()
    with pytest.raises(FrozenInstanceError):
        result.decision = Decision.ESCALATE  # type: ignore[misc]


def test_exactly_at_the_wall_clock_limit_is_allowed() -> None:
    # spec 0004: the trip is strict (`>`), so the boundary value is permitted
    assert _eval(elapsed_seconds=900.0).decision is Decision.PROCEED


def test_exactly_at_the_token_limit_is_allowed() -> None:
    assert _eval(tokens_used=200_000).decision is Decision.PROCEED


def test_one_over_the_token_limit_trips() -> None:
    assert _eval(tokens_used=200_001).decision is Decision.BUDGET_EXCEEDED
