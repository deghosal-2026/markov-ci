"""The policy gate (docs/spec/0004-policy-engine.md).

Gate evaluation is strictly ordered — **budget → attempt cap → confidence →
transition**. Order matters: a run must not be permitted one more attempt after it
has already overspent, and a budget stop must not be masked by a confidence stop.
Every rejection lands in a designed absorbing state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

A2 = "a2_escalate_to_author"
A3 = "a3_budget_exceeded"


@dataclass(frozen=True, slots=True)
class Policy:
    """Guardrail thresholds for a governed run."""

    min_confidence: float = 0.40
    max_attempts: int = 3
    max_tokens: int = 200_000
    wall_clock_seconds: int = 900

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be within [0, 1]")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if self.wall_clock_seconds < 1:
            raise ValueError("wall_clock_seconds must be >= 1")


class Decision(StrEnum):
    """Outcome of a gate evaluation."""

    PROCEED = "proceed"
    ESCALATE = "escalate"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True, slots=True)
class GateResult:
    """The gate's verdict and why it was reached."""

    decision: Decision
    reason: str
    absorbing_state: str | None = None


def evaluate(
    policy: Policy,
    *,
    attempt: int,
    tokens_used: int,
    elapsed_seconds: float,
    next_success_probability: float,
) -> GateResult:
    """Evaluate the gate for the attempt about to run (1-based)."""
    if tokens_used > policy.max_tokens:
        return GateResult(
            decision=Decision.BUDGET_EXCEEDED,
            reason=(
                f"token budget exceeded: {tokens_used} > {policy.max_tokens}"
            ),
            absorbing_state=A3,
        )
    if elapsed_seconds > policy.wall_clock_seconds:
        return GateResult(
            decision=Decision.BUDGET_EXCEEDED,
            reason=(
                f"wall-clock budget exceeded: {elapsed_seconds:.0f}s > "
                f"{policy.wall_clock_seconds}s"
            ),
            absorbing_state=A3,
        )
    if attempt > policy.max_attempts:
        return GateResult(
            decision=Decision.ESCALATE,
            reason=(
                f"attempt cap reached: attempt {attempt} > {policy.max_attempts}"
            ),
            absorbing_state=A2,
        )
    if next_success_probability < policy.min_confidence:
        return GateResult(
            decision=Decision.ESCALATE,
            reason=(
                f"confidence below threshold: {next_success_probability:.2f} < "
                f"{policy.min_confidence:.2f}"
            ),
            absorbing_state=A2,
        )
    return GateResult(
        decision=Decision.PROCEED,
        reason=f"attempt {attempt} permitted",
    )
