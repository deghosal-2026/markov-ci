"""The governed transition loop (docs/spec/0011-engine-runtime.md §1).

Triage → assemble → policy gates → adapter repair → guardrails → sandbox →
next hop or absorption. The gate is evaluated in strict order (budget → cap →
confidence), so every path terminates in one of the three designed absorbing
states — absorption by construction.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from markov_ci.agents import AgentAdapter, RepairContext
from markov_ci.engine.sandbox import SandboxResult
from markov_ci.guardrails import check_paths, check_test_modification
from markov_ci.policy import A2, A3, Decision, Policy, evaluate
from markov_ci.telemetry import RunResult, TransitionEvent, utc_now
from markov_ci.telemetry.events import JsonlSink
from markov_ci.triage import FailureCategory

A1 = "a1_ready_for_human_review"


class SandboxLike(Protocol):
    """The subset of `Sandbox` the loop depends on."""

    def apply_and_test(
        self, diff: str, command: Sequence[str], *, timeout: int = ...,
    ) -> SandboxResult: ...


class SinkLike(Protocol):
    def emit(self, event: TransitionEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class LoopConfig:
    """Everything the loop needs beyond the adapter and sandbox."""

    policy: Policy
    success_curve: tuple[float, ...]
    allow_write: tuple[str, ...]
    deny_write: tuple[str, ...]
    failing_command: tuple[str, ...]
    regression_command: tuple[str, ...]


def _confidence(config: LoopConfig, attempt: int) -> float:
    index = attempt - 1
    if 0 <= index < len(config.success_curve):
        return config.success_curve[index]
    return 0.0


def _bump(visits: dict[str, int], state: str) -> None:
    visits[state] = visits.get(state, 0) + 1


def run_loop(  # noqa: PLR0913
    *,
    adapter: AgentAdapter,
    category: FailureCategory,
    context: str,
    config: LoopConfig,
    sandbox: SandboxLike,
    run_id: str,
    commit_sha: str = "",
    pr_number: int | None = None,
    sink: SinkLike | None = None,
    patch_branch: str | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> RunResult:
    """Run the governed loop and return the full evidence trail."""
    started = clock()
    tokens = 0
    visits: dict[str, int] = {}
    guardrail_report: list[str] = []
    mandatory_review = False
    absorbing: str | None = None
    current = "s1_failure_triage"
    attempt = 1

    def emit(to_state: str, hop_attempt: int) -> None:
        nonlocal current
        if sink is not None:
            sink.emit(
                TransitionEvent(
                    event="transition",
                    run_id=run_id,
                    commit_sha=commit_sha,
                    pr_number=pr_number,
                    from_state=current,
                    to_state=to_state,
                    duration_ms=0,
                    tokens_used=tokens,
                    failure_category=category.value,
                    attempt=hop_attempt,
                    adapter=adapter.id,
                    ts=utc_now(),
                ),
            )
        current = to_state

    _bump(visits, current)
    while absorbing is None:
        gate = evaluate(
            config.policy,
            attempt=attempt,
            tokens_used=tokens,
            elapsed_seconds=clock() - started,
            next_success_probability=_confidence(config, attempt),
        )
        if gate.decision is not Decision.PROCEED:
            absorbing = gate.absorbing_state or A2
            emit(absorbing, attempt)
            _bump(visits, absorbing)
            break

        agent_state = f"s2_agent_reasoning#{attempt}"
        emit(agent_state, attempt)
        _bump(visits, agent_state)

        proposal = adapter.repair(
            RepairContext(
                category=category,
                attempt=attempt,
                max_attempts=config.policy.max_attempts,
                context=context,
            ),
        )
        tokens += proposal.tokens_used

        allowed = check_paths(
            proposal.files_changed,
            allow_write=config.allow_write,
            deny_write=config.deny_write,
        )
        if not allowed.allowed:
            guardrail_report.extend(allowed.offending)
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        tmr = check_test_modification(proposal.diff)
        if tmr.stop:
            guardrail_report.append(tmr.reason)
            mandatory_review = True
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        if not proposal.diff:
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        sandbox_state = f"s3_sandbox_validation#{attempt}"
        emit(sandbox_state, attempt)
        _bump(visits, sandbox_state)

        validation = sandbox.apply_and_test(proposal.diff, config.failing_command)
        if not validation.applied:
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break
        if not validation.passed:
            attempt += 1
            continue

        emit("s4_regression_check", attempt)
        _bump(visits, "s4_regression_check")
        regression = sandbox.apply_and_test(proposal.diff, config.regression_command)
        absorbing = A1 if regression.passed else A2
        emit(absorbing, attempt)
        _bump(visits, absorbing)

    return RunResult(
        absorbing_state=absorbing,
        visits=visits,
        tokens_used=tokens,
        wall_clock_ms=int((clock() - started) * 1000),
        guardrail_report=tuple(guardrail_report),
        events_path=None,
        patch_branch=patch_branch,
        mandatory_review=mandatory_review,
        run_id=run_id,
    )


__all__ = ["A1", "A2", "A3", "JsonlSink", "LoopConfig", "run_loop"]
