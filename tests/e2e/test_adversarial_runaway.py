"""ADR-0004 falsifier — the e2e runaway proof (docs/explanations/design-review.md §3).

The chain promises that even a config whose priors swear the agent always
succeeds (``success = [1.0, 1.0, 1.0]``) cannot make the governed loop run
away. This is the end-to-end companion of the matrix-level property test in
``tests/unit/model/test_properties.py``: worktree validation rejects every patch, and
the attempt cap absorbs the run in ``a2`` after exactly ``max_attempts``
reasoning visits — termination is a theorem, not a timeout.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from markov_ci.cli import app
from markov_ci.data import default_config_path

RUNNER = CliRunner()

JUNIT = (
    '<testsuites><testsuite><testcase name="test_broken" classname="pkg">'
    '<failure message="AssertionError: 1 != 2" type="AssertionError">trace</failure>'
    "</testcase></testsuite></testsuites>"
)

# The canned SimulatedAgent patch flips `return 1` to `return 2`; this check
# demands 3, so no attempt can ever pass worktree validation.
CHECK = (
    "import sys\nsys.path.insert(0, '.')\n"
    "from src.example import broken\n"
    "assert broken() == 3, 'not fixed'\n"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "src").mkdir()
    (path / "src" / "example.py").write_text(
        "def broken():\n    return 1\n", encoding="utf-8",
    )
    (path / "check.py").write_text(CHECK, encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "init")
    return path


def _adversarial_config(tmp_path: Path) -> Path:
    """The packaged default, with priors that promise success on every attempt."""
    text = default_config_path().read_text(encoding="utf-8")
    assert "success: [0.74, 0.45, 0.15]" in text  # the unit_assertion curve we hijack
    adversarial = text.replace(
        "success: [0.74, 0.45, 0.15]", "success: [1.0, 1.0, 1.0]",
    ).replace("path: .markov-ci/events.jsonl", f"path: {tmp_path}/events.jsonl")
    path = tmp_path / "adversarial.yaml"
    path.write_text(adversarial, encoding="utf-8")
    return path


def test_perfect_priors_still_terminate_at_the_cap(repo: Path, tmp_path: Path) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        [
            "run", str(_adversarial_config(tmp_path)),
            "--junit", str(junit),
            "--repo", str(repo),
            "--seed", "1",
            "--failing-command", f'"{sys.executable}" check.py',
            "--json",
        ],
    )
    assert result.exit_code == 1, result.stdout  # a2_escalate_to_author
    payload = json.loads(result.stdout)
    assert payload["absorbing_state"] == "a2_escalate_to_author"
    assert payload["tokens_used"] == 0  # termination is structural, not budgetary
    reasoning = [s for s in payload["visits"] if s.startswith("s2_agent_reasoning#")]
    assert reasoning == [
        "s2_agent_reasoning#1", "s2_agent_reasoning#2", "s2_agent_reasoning#3",
    ]

    events = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(events) == 7  # 3 × (reasoning, validation) + the final absorbing hop
    assert events[-1]["to_state"] == "a2_escalate_to_author"
    assert events[-1]["attempt"] == 4  # the attempt-cap gate, not low confidence
