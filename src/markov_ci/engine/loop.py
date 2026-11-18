"""The governed transition loop (docs/spec/0011-engine-runtime.md §1).

Triage → assemble → policy gates → adapter repair → guardrails → worktree validation →
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
from markov_ci.agents.harness import HarnessTimeout
from markov_ci.engine.validation import ValidationResult
from markov_ci.guardrails import check_paths, check_test_modification
from markov_ci.guardrails.diffpaths import parse_diff_paths, symlink_paths
from markov_ci.policy import A2, A3, Decision, Policy, evaluate
from markov_ci.telemetry import RunResult, TransitionEvent, utc_now
from markov_ci.telemetry.events import JsonlSink
from markov_ci.triage import FailureCategory
from markov_ci.triage.minimize import minimize

A1 = "a1_ready_for_human_review"


class ValidatorLike(Protocol):
    """The subset of `WorktreeValidator` the loop depends on."""

    def apply_and_test(
        self,
        diff: str,
        command: Sequence[str],
        *,
        timeout: int = ...,
        allow_write: Sequence[str] = ...,
        deny_write: Sequence[str] = ...,
        env_allow: Sequence[str] = ...,
    ) -> ValidationResult: ...


class SinkLike(Protocol):
    def emit(self, event: TransitionEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class LoopConfig:
    """Everything the loop needs beyond the adapter and worktree validation."""

    policy: Policy
    success_curve: tuple[float, ...]
    allow_write: tuple[str, ...]
    deny_write: tuple[str, ...]
    failing_command: tuple[str, ...]
    regression_command: tuple[str, ...]
    env_allow: tuple[str, ...] = ()
    validation_timeout: int = 600


def _confidence(config: LoopConfig, attempt: int) -> float:
    index = attempt - 1
    if 0 <= index < len(config.success_curve):
        return config.success_curve[index]
    return 0.0


def _summarize(output: str, limit: int = 400) -> str:
    """A bounded summary of validation output (spec 0011 §2, M13.25)."""
    collapsed = " ".join(output.split())
    return collapsed[:limit]


def _bump(visits: dict[str, int], state: str) -> None:
    visits[state] = visits.get(state, 0) + 1


def run_loop(  # noqa: PLR0913
    *,
    adapter: AgentAdapter,
    category: FailureCategory,
    context: str,
    config: LoopConfig,
    validator: ValidatorLike,
    run_id: str,
    commit_sha: str = "",
    pr_number: int | None = None,
    sink: SinkLike | None = None,
    patch_branch: str | None = None,
    config_hash: str | None = None,
    model_version: str | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> RunResult:
    """Run the governed loop and return the full evidence trail."""
    started = clock()
    tokens: int | None = None
    visits: dict[str, int] = {}
    guardrail_report: list[str] = []
    mandatory_review = False
    absorbing: str | None = None
    validated_patch: str | None = None
    retry_context: str | None = None
    retry_diff: str | None = None
    validation_output: str | None = None
    current = "s1_failure_triage"
    attempt = 1

    def emit(
        to_state: str,
        hop_attempt: int,
        *,
        event: str = "transition",
        gate_rejected: str | None = None,
    ) -> None:
        nonlocal current
        if sink is not None:
            sink.emit(
                TransitionEvent(
                    event=event,
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
                    synthetic=adapter.id == "simulated",
                    gate_rejected=gate_rejected,
                    config_hash=config_hash,
                    model_version=model_version,
                ),
            )
        current = to_state

    _bump(visits, current)
    while absorbing is None:
        gate = evaluate(
            config.policy,
            attempt=attempt,
            tokens_used=tokens or 0,
            elapsed_seconds=clock() - started,
            next_success_probability=_confidence(config, attempt),
        )
        if gate.decision is not Decision.PROCEED:
            absorbing = gate.absorbing_state or A2
            emit(absorbing, attempt, event="gate_rejected", gate_rejected=gate.reason)
            _bump(visits, absorbing)
            break

        agent_state = f"s2_agent_reasoning#{attempt}"
        emit(agent_state, attempt)
        _bump(visits, agent_state)

        remaining = max(
            1, int(config.policy.wall_clock_seconds - (clock() - started)),
        )
        try:
            proposal = adapter.repair(
                RepairContext(
                    category=category,
                    attempt=attempt,
                    max_attempts=config.policy.max_attempts,
                    context=retry_context or context,
                    diff=retry_diff,
                    timeout=remaining,
                ),
            )
        except HarnessTimeout:
            absorbing = A3
            emit(A3, attempt)
            _bump(visits, A3)
            break
        if proposal.tokens_used is not None:
            tokens = (tokens or 0) + proposal.tokens_used

        if not proposal.diff.strip():
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        symlinks = symlink_paths(proposal.diff)
        if symlinks:
            guardrail_report.append(
                f"symlink creation denied: {', '.join(symlinks)}",
            )
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        derived = parse_diff_paths(proposal.diff)
        if not derived:
            guardrail_report.append("could not determine the paths this patch touches")
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break

        touched = tuple(dict.fromkeys((*derived, *proposal.files_changed)))
        allowed = check_paths(
            touched,
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

        validation_state = f"s3_sandbox_validation#{attempt}"
        emit(validation_state, attempt)
        _bump(visits, validation_state)

        validation = validator.apply_and_test(
            proposal.diff,
            config.failing_command,
            timeout=min(config.validation_timeout, remaining),
            allow_write=config.allow_write,
            deny_write=config.deny_write,
            env_allow=config.env_allow,
        )
        if validation.timed_out:
            absorbing = A3
            emit(A3, attempt)
            _bump(visits, A3)
            break
        if not validation.applied:
            validation_output = _summarize(validation.output)
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break
        if validation.guardrail_report:
            guardrail_report.extend(validation.guardrail_report)
            absorbing = A2
            emit(A2, attempt)
            _bump(visits, A2)
            break
        if not validation.passed:
            # feed the previous validation output + diff into the next attempt
            retry_context = minimize([], logs=validation.output).text
            retry_diff = proposal.diff
            validation_output = _summarize(validation.output)
            attempt += 1
            continue

        if not config.regression_command:
            # no explicit broader regression command → skip s4 (M13.31)
            validated_patch = proposal.diff
            absorbing = A1
            emit(A1, attempt)
            _bump(visits, A1)
            break

        emit("s4_regression_check", attempt)
        _bump(visits, "s4_regression_check")
        validated_patch = proposal.diff
        regression = validator.apply_and_test(
            proposal.diff,
            config.regression_command,
            allow_write=config.allow_write,
            deny_write=config.deny_write,
            env_allow=config.env_allow,
        )
        if regression.guardrail_report:
            guardrail_report.extend(regression.guardrail_report)
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
        patch=validated_patch if absorbing == A1 else None,
        validation_output=validation_output,
    )


__all__ = ["A1", "A2", "A3", "JsonlSink", "LoopConfig", "run_loop"]
