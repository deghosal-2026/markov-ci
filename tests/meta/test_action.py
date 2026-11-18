"""M10.1 (#46) — the root composite Action (F15).

Contract: docs/how-to/integrate-github-actions.md. The Action wraps the CLI,
governs a run, and exposes the documented inputs/outputs. Its run script is
exercised offline against a temp repo — no GitHub runner required.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTION_YML = ROOT / "action.yml"
RUN_SH = ROOT / "action" / "run.sh"

JUNIT = (
    '<testsuites><testsuite><testcase name="test_broken" classname="pkg">'
    '<failure message="AssertionError: 1 != 2" type="AssertionError">trace</failure>'
    "</testcase></testsuite></testsuites>"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_action_is_a_composite_with_the_documented_contract() -> None:
    action = yaml.safe_load(ACTION_YML.read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    inputs = action["inputs"]
    assert {"config", "junit", "seed", "adapter", "max-tokens", "wall-clock"} <= set(inputs)
    assert inputs["junit"]["required"] is True
    outputs = action["outputs"]
    assert {"absorbing-state", "run-id", "patch-branch", "events-path"} <= set(outputs)


def test_action_run_script_exists() -> None:
    assert RUN_SH.is_file()


def test_run_script_governs_a_repo_and_writes_outputs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    (repo / "src").mkdir()
    (repo / "src" / "example.py").write_text(
        "def broken():\n    return 1\n", encoding="utf-8",
    )
    (repo / "test_example.py").write_text(
        "from src.example import broken\n\n\ndef test_broken() -> None:\n"
        "    assert broken() == 2\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "init")
    (repo / "report.xml").write_text(JUNIT, encoding="utf-8")

    out = tmp_path / "github_output"
    out.write_text("", encoding="utf-8")
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""),
        "GITHUB_OUTPUT": str(out),
        "INPUT_JUNIT": "report.xml",
        "INPUT_SEED": "1",
    }
    result = subprocess.run(
        ["bash", str(RUN_SH)], cwd=repo, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    outputs = dict(
        line.split("=", 1)
        for line in out.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    assert outputs["absorbing-state"] == "a1_ready_for_human_review"
    assert outputs["exit-code"] == "0"
    assert outputs["run-id"]
    assert outputs["patch-branch"].startswith("ai-fix/")
