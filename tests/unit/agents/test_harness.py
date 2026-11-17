"""M4.3 (#24) — headless harness adapter (docs/spec/0006 §3, ADR-0007).

All tests inject a fake runner, so they are fully offline.
"""

from __future__ import annotations

import subprocess

import pytest

from markov_ci.agents import AgentAdapter, PatchProposal, RepairContext
from markov_ci.agents.harness import (
    HarnessAgent,
    HarnessError,
    HarnessSpec,
    HarnessTimeout,
    parse_harness_output,
)
from markov_ci.triage import FailureCategory

FENCED = """some chatter
```diff
--- a/src/example.py
+++ b/src/example.py
@@ -1 +1 @@
-old
+new
```
tokens_used: 1834
"""


class FakeRunner:
    def __init__(
        self, stdout: str = "", returncode: int = 0, raises: Exception | None = None,
    ) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.raises = raises
        self.calls: list[tuple[str, int]] = []

    def __call__(self, command: str, *, timeout: int) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, timeout))
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(
            args=command, returncode=self.returncode, stdout=self.stdout, stderr="",
        )


def _context() -> RepairContext:
    return RepairContext(
        category=FailureCategory.UNIT_ASSERTION,
        attempt=1,
        max_attempts=3,
        context="AssertionError: 1 != 2",
    )


def _agent(runner: FakeRunner, template: str = 'harness --msg "%PROMPT%"') -> HarnessAgent:
    return HarnessAgent(HarnessSpec(command_template=template, timeout_seconds=120), runner=runner)


def test_is_an_adapter() -> None:
    assert isinstance(_agent(FakeRunner()), AgentAdapter)


def test_id_comes_from_the_spec() -> None:
    spec = HarnessSpec(command_template="x %PROMPT%", id="claude-code")
    assert HarnessAgent(spec, runner=FakeRunner()).id == "claude-code"


def test_prompt_is_substituted_into_the_command() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context())
    command, _ = runner.calls[0]
    assert "%PROMPT%" not in command
    assert "AssertionError" in command


def test_timeout_is_passed_to_the_runner() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context())
    assert runner.calls[0][1] == 120


def test_diff_is_extracted_from_a_fenced_block() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert isinstance(proposal, PatchProposal)
    assert "+new" in proposal.diff
    assert "-old" in proposal.diff


def test_token_usage_is_parsed() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert proposal.tokens_used == 1834


def test_files_changed_are_derived_from_the_diff() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert "src/example.py" in proposal.files_changed


def test_non_zero_exit_yields_no_patch() -> None:
    proposal = _agent(FakeRunner(stdout="", returncode=2)).repair(_context())
    assert proposal.diff == ""
    assert "exit" in proposal.rationale


def test_timeout_raises_harness_timeout() -> None:
    runner = FakeRunner(raises=subprocess.TimeoutExpired(cmd="x", timeout=1))
    with pytest.raises(HarnessTimeout):
        _agent(runner).repair(_context())


def test_missing_harness_raises_harness_error() -> None:
    runner = FakeRunner(raises=FileNotFoundError("no such harness"))
    with pytest.raises(HarnessError):
        _agent(runner).repair(_context())


def test_parse_harness_output_handles_no_diff() -> None:
    diff, tokens = parse_harness_output("just some logs, no patch")
    assert diff == ""
    assert tokens == 0


def test_parse_harness_output_reads_tokens_without_a_diff() -> None:
    _, tokens = parse_harness_output('{"tokens_used": 42}')
    assert tokens == 42
