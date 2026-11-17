"""M6.2 (#30) — the governed transition loop (docs/spec/0011-engine-runtime.md §1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from markov_ci.agents import PatchProposal, RepairContext
from markov_ci.engine.loop import A1, A2, A3, LoopConfig, run_loop
from markov_ci.engine.sandbox import SandboxResult
from markov_ci.policy import Policy
from markov_ci.telemetry import RunResult, TransitionEvent
from markov_ci.triage import FailureCategory

GOOD_DIFF = "--- a/src/app.py\n+++ b/src/app.py\n@@\n-old\n+new\n"


class FakeAdapter:
    id = "fake"

    def __init__(self, diff: str = GOOD_DIFF, files: tuple[str, ...] = ("src/app.py",)) -> None:
        self._diff = diff
        self._files = files
        self.calls = 0

    def repair(self, ctx: RepairContext) -> PatchProposal:
        self.calls += 1
        return PatchProposal(
            diff=self._diff, rationale="", tokens_used=10, files_changed=self._files,
        )


class FakeSandbox:
    def __init__(self, results: Sequence[SandboxResult]) -> None:
        self._results = list(results)
        self.calls = 0

    def apply_and_test(
        self, diff: str, command: Sequence[str], *, timeout: int = 600,
    ) -> SandboxResult:
        self.calls += 1
        return self._results.pop(0)


@dataclass
class Sink:
    events: list[tuple[str, str, int]] = field(default_factory=list)

    def emit(self, event: TransitionEvent) -> None:
        self.events.append((event.from_state, event.to_state, event.attempt))


def _config(
    *,
    success_curve: tuple[float, ...] = (0.9, 0.9, 0.9),
    max_tokens: int = 200_000,
) -> LoopConfig:
    return LoopConfig(
        policy=Policy(max_tokens=max_tokens),
        success_curve=success_curve,
        allow_write=("src/**", "tests/**"),
        deny_write=(),
        failing_command=("pytest", "tests/unit"),
        regression_command=("pytest",),
    )


def _run(
    *,
    adapter: FakeAdapter | None = None,
    sandbox: FakeSandbox | None = None,
    config: LoopConfig | None = None,
    sink: Sink | None = None,
) -> RunResult:
    return run_loop(
        adapter=adapter or FakeAdapter(),
        category=FailureCategory.UNIT_ASSERTION,
        context="AssertionError: 1 != 2",
        config=config or _config(),
        sandbox=sandbox or FakeSandbox(
            [SandboxResult(True, True, ""), SandboxResult(True, True, "")],
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
    sandbox = FakeSandbox([SandboxResult(True, False, "") for _ in range(10)])
    result = _run(sandbox=sandbox)
    assert result.absorbing_state == A2


def test_budget_trip_absorbs_in_a3() -> None:
    # validation keeps failing, each attempt spends 10 tokens; the budget trips
    sandbox = FakeSandbox([SandboxResult(True, False, "") for _ in range(10)])
    result = _run(sandbox=sandbox, config=_config(max_tokens=15))
    assert result.absorbing_state == A3


def test_failed_validation_loops_back_then_succeeds() -> None:
    sandbox = FakeSandbox(
        [
            SandboxResult(True, False, ""),  # attempt 1 fails
            SandboxResult(True, True, ""),   # attempt 2 passes
            SandboxResult(True, True, ""),   # regression passes
        ],
    )
    result = _run(sandbox=sandbox)
    assert result.absorbing_state == A1
    assert sandbox.calls == 3


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
    sandbox = FakeSandbox([SandboxResult(False, False, "no apply")])
    assert _run(sandbox=sandbox).absorbing_state == A2


def test_no_patch_produced_absorbs_in_a2() -> None:
    assert _run(adapter=FakeAdapter(diff="")).absorbing_state == A2


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


def test_result_carries_the_run_id() -> None:
    result = _run()
    assert result.run_id == "run_test"
    assert result.as_dict()["run_id"] == "run_test"
