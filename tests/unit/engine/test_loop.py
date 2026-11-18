"""M6.2 (#30) — the governed transition loop (docs/spec/0011-engine-runtime.md §1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from markov_ci.agents import AgentAdapter, PatchProposal, RepairContext
from markov_ci.engine.loop import A1, A2, A3, LoopConfig, run_loop
from markov_ci.engine.validation import ValidationResult
from markov_ci.policy import Policy
from markov_ci.telemetry import RunResult, TransitionEvent
from markov_ci.triage import FailureCategory

GOOD_DIFF = "--- a/src/app.py\n+++ b/src/app.py\n@@\n-old\n+new\n"


class FakeAdapter:
    id = "fake"

    def __init__(
        self,
        diff: str = GOOD_DIFF,
        files: tuple[str, ...] = ("src/app.py",),
        raises: Exception | None = None,
    ) -> None:
        self._diff = diff
        self._files = files
        self._raises = raises
        self.calls = 0
        self.contexts: list[RepairContext] = []

    def repair(self, ctx: RepairContext) -> PatchProposal:
        self.calls += 1
        self.contexts.append(ctx)
        if self._raises is not None:
            raise self._raises
        return PatchProposal(
            diff=self._diff, rationale="", tokens_used=10, files_changed=self._files,
        )


class FakeValidator:
    def __init__(self, results: Sequence[ValidationResult]) -> None:
        self._results = list(results)
        self.calls = 0
        self.kwargs: list[dict[str, object]] = []

    def apply_and_test(
        self,
        diff: str,
        command: Sequence[str],
        *,
        timeout: int = 600,
        allow_write: Sequence[str] = ("**",),
        deny_write: Sequence[str] = (),
        env_allow: Sequence[str] = (),
    ) -> ValidationResult:
        self.calls += 1
        self.kwargs.append({"env_allow": tuple(env_allow), "timeout": timeout})
        return self._results.pop(0)


@dataclass
class Sink:
    events: list[tuple[str, str, int]] = field(default_factory=list)

    def emit(self, event: TransitionEvent) -> None:
        self.events.append((event.from_state, event.to_state, event.attempt))


class SinkLike(Protocol):
    def emit(self, event: TransitionEvent) -> None: ...


def _config(
    *,
    success_curve: tuple[float, ...] = (0.9, 0.9, 0.9),
    max_tokens: int = 200_000,
    env_allow: tuple[str, ...] = (),
    wall_clock: int = 900,
    regression_command: tuple[str, ...] = ("pytest",),
) -> LoopConfig:
    return LoopConfig(
        policy=Policy(max_tokens=max_tokens, wall_clock_seconds=wall_clock),
        success_curve=success_curve,
        allow_write=("src/**", "tests/**"),
        deny_write=(),
        failing_command=("pytest", "tests/unit"),
        regression_command=regression_command,
        env_allow=env_allow,
    )


def _run(
    *,
    adapter: AgentAdapter | None = None,
    validator: FakeValidator | None = None,
    config: LoopConfig | None = None,
    sink: SinkLike | None = None,
) -> RunResult:
    return run_loop(
        adapter=adapter or FakeAdapter(),
        category=FailureCategory.UNIT_ASSERTION,
        context="AssertionError: 1 != 2",
        config=config or _config(),
        validator=validator or FakeValidator(
            [ValidationResult(True, True, ""), ValidationResult(True, True, "")],
        ),
        sink=sink,
        run_id="run_test",
        commit_sha="abc",
        pr_number=1,
        patch_branch="ai-fix/pr-1",
    )


def test_happy_path_absorbs_in_a1() -> None:
    result = _run()
    assert result.absorbing_state == A1


def test_low_confidence_escalates_before_calling_the_agent() -> None:
    adapter = FakeAdapter()
    result = _run(adapter=adapter, config=_config(success_curve=(0.1, 0.1, 0.1)))
    assert result.absorbing_state == A2
    assert adapter.calls == 0


def test_attempt_cap_escalates() -> None:
    validator = FakeValidator([ValidationResult(True, False, "") for _ in range(10)])
    result = _run(validator=validator)
    assert result.absorbing_state == A2


def test_budget_trip_absorbs_in_a3() -> None:
    # validation keeps failing, each attempt spends 10 tokens; the budget trips
    validator = FakeValidator([ValidationResult(True, False, "") for _ in range(10)])
    result = _run(validator=validator, config=_config(max_tokens=15))
    assert result.absorbing_state == A3


def test_failed_validation_loops_back_then_succeeds() -> None:
    validator = FakeValidator(
        [
            ValidationResult(True, False, ""),  # attempt 1 fails
            ValidationResult(True, True, ""),   # attempt 2 passes
            ValidationResult(True, True, ""),   # regression passes
        ],
    )
    result = _run(validator=validator)
    assert result.absorbing_state == A1
    assert validator.calls == 3


def test_guardrail_denial_absorbs_in_a2() -> None:
    adapter = FakeAdapter(files=(".github/workflows/ci.yml",))
    result = _run(adapter=adapter)
    assert result.absorbing_state == A2
    assert result.guardrail_report


def test_test_weakening_absorbs_in_a2() -> None:
    deleting = "--- a/tests/test_a.py\n+++ b/tests/test_a.py\n@@\n-    assert value == 1\n"
    result = _run(adapter=FakeAdapter(diff=deleting, files=("tests/test_a.py",)))
    assert result.absorbing_state == A2
    assert any("assertion" in note for note in result.guardrail_report)


def test_test_weakening_flags_mandatory_review() -> None:
    deleting = "--- a/tests/test_a.py\n+++ b/tests/test_a.py\n@@\n-    assert value == 1\n"
    result = _run(adapter=FakeAdapter(diff=deleting, files=("tests/test_a.py",)))
    assert result.mandatory_review is True
    assert result.as_dict()["mandatory_review"] is True


def test_clean_run_does_not_flag_mandatory_review() -> None:
    assert _run().mandatory_review is False


def test_patch_that_does_not_apply_absorbs_in_a2() -> None:
    validator = FakeValidator([ValidationResult(False, False, "no apply")])
    assert _run(validator=validator).absorbing_state == A2


def test_no_patch_produced_absorbs_in_a2() -> None:
    assert _run(adapter=FakeAdapter(diff="")).absorbing_state == A2


def test_non_empty_diff_with_no_derivable_paths_fails_closed() -> None:
    # M13.8 (#92): a non-empty diff whose paths cannot be derived denies.
    adapter = FakeAdapter(diff="this is not a diff\n", files=())
    result = _run(adapter=adapter)
    assert result.absorbing_state == A2
    assert any("could not determine" in note for note in result.guardrail_report)


def test_derived_paths_are_checked_even_when_declared_paths_are_clean() -> None:
    # the declared list lies (src only) but the diff touches .github
    sneaky = (
        "--- a/.github/workflows/ci.yml\n"
        "+++ b/.github/workflows/ci.yml\n"
        "@@ -1 +1 @@\n-x\n+y\n"
    )
    result = _run(adapter=FakeAdapter(diff=sneaky, files=("src/app.py",)))
    assert result.absorbing_state == A2
    assert result.guardrail_report


def test_symlink_creation_is_denied_and_recorded() -> None:
    symlink = (
        "diff --git a/src/link b/src/link\n"
        "new file mode 120000\n"
        "--- /dev/null\n"
        "+++ b/src/link\n"
        "@@ -0,0 +1 @@\n"
        "+/etc/passwd\n"
    )
    result = _run(adapter=FakeAdapter(diff=symlink, files=("src/link",)))
    assert result.absorbing_state == A2
    assert any("symlink" in note for note in result.guardrail_report)


def test_events_are_emitted_per_hop() -> None:
    sink = Sink()
    _run(sink=sink)
    assert sink.events
    assert sink.events[-1][1] == A1


def test_visits_are_recorded() -> None:
    result = _run()
    assert result.visits
    assert any(state.startswith("s2_agent_reasoning") for state in result.visits)


def test_result_carries_tokens_and_branch() -> None:
    result = _run()
    assert result.tokens_used == 10
    assert result.patch_branch == "ai-fix/pr-1"


def test_a1_keeps_the_validated_patch() -> None:
    # M13.23 (#107): a1 no longer discards the fix.
    result = _run()
    assert result.absorbing_state == A1
    assert result.patch is not None
    assert "-old" in result.patch
    assert "+new" in result.patch


def test_a2_discards_the_patch() -> None:
    result = _run(adapter=FakeAdapter(files=(".github/workflows/ci.yml",)))
    assert result.absorbing_state == A2
    assert result.patch is None


def test_result_carries_the_run_id() -> None:
    result = _run()
    assert result.run_id == "run_test"
    assert result.as_dict()["run_id"] == "run_test"


def test_loop_forwards_the_env_allowlist_to_validation() -> None:
    # M13.14 (#98): config-listed env vars reach the validation child.
    validator = FakeValidator([ValidationResult(True, True, ""), ValidationResult(True, True, "")])
    _run(validator=validator, config=_config(env_allow=("MY_PROVIDER_KEY",)))
    assert validator.kwargs[0]["env_allow"] == ("MY_PROVIDER_KEY",)


def test_remaining_budget_is_passed_to_validation() -> None:
    # M13.20 (#104): every call gets min(configured_timeout, remaining_wall_clock).
    validator = FakeValidator([ValidationResult(True, True, ""), ValidationResult(True, True, "")])
    _run(validator=validator, config=_config(wall_clock=100))
    timeout = validator.kwargs[0]["timeout"]
    assert isinstance(timeout, int)
    assert timeout <= 100


def test_repair_context_carries_the_remaining_budget() -> None:
    adapter = FakeAdapter()
    _run(adapter=adapter, config=_config(wall_clock=123))
    assert adapter.contexts[0].timeout is not None
    assert adapter.contexts[0].timeout <= 123


def test_validation_timeout_absorbs_in_a3_with_an_event() -> None:
    sink = Sink()
    validator = FakeValidator([ValidationResult(True, False, "timed out", timed_out=True)])
    result = _run(validator=validator, sink=sink)
    assert result.absorbing_state == A3
    assert sink.events[-1][1] == A3


def test_harness_timeout_absorbs_in_a3_with_an_event() -> None:
    from markov_ci.agents.harness import HarnessTimeout

    sink = Sink()
    result = _run(adapter=FakeAdapter(raises=HarnessTimeout("slow")), sink=sink)
    assert result.absorbing_state == A3
    assert sink.events[-1][1] == A3


def test_unreported_tokens_are_null_in_the_result() -> None:
    # M13.21 (#105): a harness that reports no usage yields tokens_used=None.
    class NoUsageAdapter:
        id = "nousage"

        def repair(self, ctx: RepairContext) -> PatchProposal:
            return PatchProposal(diff=GOOD_DIFF, rationale="", tokens_used=None)

    result = _run(adapter=NoUsageAdapter())
    assert result.absorbing_state == A1
    assert result.tokens_used is None


def test_retry_context_carries_the_previous_validation_output_and_diff() -> None:
    # M13.25 (#109): the next attempt learns what actually went wrong.
    validator = FakeValidator(
        [
            ValidationResult(True, False, "ModuleNotFoundError: no module named x"),
            ValidationResult(True, True, ""),
            ValidationResult(True, True, ""),
        ],
    )
    adapter = FakeAdapter()
    result = _run(adapter=adapter, validator=validator)
    assert result.absorbing_state == A1
    assert adapter.calls == 2
    retry = adapter.contexts[1]
    assert "ModuleNotFoundError" in retry.context
    assert retry.diff == GOOD_DIFF
    assert result.validation_output is not None
    assert "ModuleNotFoundError" in result.validation_output


def test_validation_output_is_summarized_when_a_patch_does_not_apply() -> None:
    # "agent failed" is distinguishable from "not a git repo" / "test command not found"
    validator = FakeValidator([ValidationResult(False, False, "clone failed: not a git repo")])
    result = _run(validator=validator)
    assert result.absorbing_state == A2
    assert result.validation_output is not None
    assert "not a git repo" in result.validation_output


def test_gate_rejection_is_recorded_as_a_gate_rejected_event() -> None:
    # M13.29 (#113): the gate reason is recorded on the event.

    class RecordingSink:
        def __init__(self) -> None:
            self.events: list[TransitionEvent] = []

        def emit(self, event: TransitionEvent) -> None:
            self.events.append(event)

    sink = RecordingSink()
    result = _run(config=_config(success_curve=(0.1, 0.1, 0.1)), sink=sink)
    assert result.absorbing_state == A2
    rejected = [event for event in sink.events if event.event == "gate_rejected"]
    assert rejected
    assert rejected[-1].gate_rejected is not None
    assert "confidence" in rejected[-1].gate_rejected


def test_no_regression_command_skips_s4() -> None:
    # M13.31 (#115): without an explicit broader regression command, s4 is skipped.
    validator = FakeValidator([ValidationResult(True, True, "")])
    sink = Sink()
    result = _run(validator=validator, config=_config(regression_command=()), sink=sink)
    assert result.absorbing_state == A1
    assert validator.calls == 1
    assert all(to != "s4_regression_check" for _, to, _ in sink.events)


def test_simulated_events_are_tagged_synthetic() -> None:

    class SimulatedIdAdapter(FakeAdapter):
        id = "simulated"

    class RecordingSink:
        def __init__(self) -> None:
            self.events: list[TransitionEvent] = []

        def emit(self, event: TransitionEvent) -> None:
            self.events.append(event)

    sink = RecordingSink()
    _run(adapter=SimulatedIdAdapter(), sink=sink)
    assert sink.events
    assert all(event.synthetic for event in sink.events)


def test_regression_failure_absorbs_in_a2() -> None:
    # M13.39 (#123): the s4 regression check is load-bearing.
    validator = FakeValidator(
        [
            ValidationResult(True, True, ""),   # the failing check now passes
            ValidationResult(True, False, "regression failed"),  # s4 fails
        ],
    )
    result = _run(validator=validator)
    assert result.absorbing_state == A2
    assert validator.calls == 2
