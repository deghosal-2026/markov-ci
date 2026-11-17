"""M6.4 (#32) — end-to-end `markov-ci run` on a real (tiny) repository."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from markov_ci.cli import app

RUNNER = CliRunner()

JUNIT = (
    '<testsuites><testsuite><testcase name="test_broken" classname="pkg">'
    '<failure message="AssertionError: 1 != 2" type="AssertionError">trace</failure>'
    "</testcase></testsuite></testsuites>"
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
    # matches the canned SimulatedAgent patch (def broken(): return 1 -> return 2)
    (path / "src" / "example.py").write_text("def broken():\n    return 1\n", encoding="utf-8")
    (path / "check.py").write_text(
        "import sys\nsys.path.insert(0, '.')\n"
        "from src.example import broken\n"
        "assert broken() == 2, 'not fixed'\n",
        encoding="utf-8",
    )
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "init")
    return path


def test_run_happy_path_absorbs_in_a1(repo: Path, tmp_path: Path) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        [
            "run",
            "--junit", str(junit),
            "--repo", str(repo),
            "--seed", "1",
            "--failing-command", f'"{sys.executable}" check.py',
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["absorbing_state"] == "a1_ready_for_human_review"


def test_run_wall_clock_override_absorbs_in_a3(repo: Path, tmp_path: Path) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        [
            "run", "--junit", str(junit), "--repo", str(repo), "--seed", "1",
            "--failing-command", "python3 -c 'import time,sys; time.sleep(1.5); sys.exit(1)'",
            "--wall-clock", "1", "--json",
        ],
    )
    assert result.exit_code == 3, result.stdout
    assert json.loads(result.stdout)["absorbing_state"] == "a3_budget_exceeded"


def test_run_does_not_modify_the_repository(repo: Path, tmp_path: Path) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    RUNNER.invoke(
        app,
        [
            "run",
            "--junit", str(junit),
            "--repo", str(repo),
            "--seed", "1",
            "--failing-command", f'"{sys.executable}" check.py',
        ],
    )
    assert (repo / "src" / "example.py").read_text(encoding="utf-8") == (
        "def broken():\n    return 1\n"
    )
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    )
    assert status.stdout.strip() == ""
