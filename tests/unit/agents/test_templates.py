"""M4.4 (#25) — harness templates + the shared offline conformance suite.

One conformance suite runs against every shipped template (PRD 07 / spec 0006 §3).
Each template is exercised through a stub runner, so the suite is fully offline.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from markov_ci.agents import AgentAdapter, HarnessSpec, RepairContext
from markov_ci.agents.templates import (
    TEMPLATES,
    HarnessTemplate,
    build_template_agent,
    template_spec,
)
from markov_ci.triage import FailureCategory

FENCED = (
    "```diff\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-old\n+new\n"
    "```\n"
    "tokens_used: 1234\n"
)


class StubRunner:
    def __init__(self, stdout: str = FENCED, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.calls: list[tuple[list[str], int]] = []

    def __call__(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((list(argv), timeout))
        return subprocess.CompletedProcess(
            args=list(argv), returncode=self.returncode, stdout=self.stdout, stderr="",
        )


def _context() -> RepairContext:
    return RepairContext(
        category=FailureCategory.UNIT_ASSERTION,
        attempt=1,
        max_attempts=3,
        context="AssertionError: 1 != 2",
    )


def test_the_three_named_templates_are_shipped() -> None:
    assert {"claude-code", "opencode", "aider"} <= set(TEMPLATES)


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_template_declares_its_invocation_contract(name: str) -> None:
    template = TEMPLATES[name]
    assert isinstance(template, HarnessTemplate)
    assert template.id
    assert "%PROMPT%" in template.command_template
    assert template.timeout_seconds > 0
    assert template.tested_versions  # documented (see docs/spec/0006 §3)


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_conformance_agent_is_an_adapter(name: str) -> None:
    assert isinstance(build_template_agent(name, runner=StubRunner()), AgentAdapter)


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_conformance_prompt_is_substituted(name: str) -> None:
    runner = StubRunner()
    build_template_agent(name, runner=runner).repair(_context())
    argv, _ = runner.calls[0]
    assert all("%PROMPT%" not in part for part in argv)
    assert any("AssertionError" in part for part in argv)


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_conformance_patch_and_tokens_are_parsed(name: str) -> None:
    proposal = build_template_agent(name, runner=StubRunner()).repair(_context())
    assert "+new" in proposal.diff
    assert proposal.tokens_used == 1234
    assert "src/example.py" in proposal.files_changed


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_conformance_timeout_is_bounded(name: str) -> None:
    runner = StubRunner()
    build_template_agent(name, runner=runner).repair(_context())
    assert runner.calls[0][1] == TEMPLATES[name].timeout_seconds


def test_template_spec_returns_a_harness_spec() -> None:
    assert isinstance(template_spec("claude-code"), HarnessSpec)


def test_unknown_template_name_is_rejected() -> None:
    with pytest.raises(KeyError):
        template_spec("not-a-harness")
