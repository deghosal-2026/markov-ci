"""M6.4 (#32) — end-to-end `markov-ci run` on a real (tiny) repository."""

from __future__ import annotations

import json
import os
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


@pytest.fixture(autouse=True)
def _hermetic_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run with CWD in tmp_path so telemetry never lands in the repo (M13.38)."""
    monkeypatch.chdir(tmp_path)


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


def test_run_rejects_an_invalid_harness_template_as_invalid_config(
    repo: Path, tmp_path: Path,
) -> None:
    # M13.2 (#86): a broken command_template fails at config load (exit 4), not
    # mid-run (exit 2).
    from markov_ci.data import default_config_path

    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    config = tmp_path / "config.yaml"
    config.write_text(
        default_config_path()
        .read_text(encoding="utf-8")
        .replace(
            "  adapter: simulated\n",
            "  adapter: harness\n  harness:\n    command_template: 'harness --msg fixed'\n",
        ),
        encoding="utf-8",
    )
    result = RUNNER.invoke(
        app,
        ["run", str(config), "--junit", str(junit), "--repo", str(repo)],
    )
    assert result.exit_code == 4, result.stdout
    assert "%PROMPT%" in result.stdout


def test_run_emits_a_terminal_event_on_ineligible_triage(
    repo: Path, tmp_path: Path,
) -> None:
    # M13.22 (#106): an exit outside the loop still writes a terminal event.
    from markov_ci.data import default_config_path

    junit = tmp_path / "report.xml"
    junit.write_text(
        '<testsuites><testsuite><testcase name="t" classname="pkg">'
        '<failure message="flaky network" type="Timeout">trace</failure>'
        "</testcase></testsuite></testsuites>",
        encoding="utf-8",
    )
    events = tmp_path / "events.jsonl"
    config = tmp_path / "config.yaml"
    config.write_text(
        default_config_path().read_text(encoding="utf-8").replace(
            "  path: .markov-ci/events.jsonl", f"  path: {events}",
        ),
        encoding="utf-8",
    )
    result = RUNNER.invoke(
        app, ["run", str(config), "--junit", str(junit), "--repo", str(repo)],
    )
    assert result.exit_code == 1, result.stdout
    lines = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert lines, "no terminal event was written"
    assert lines[-1]["to_state"] == "a2_escalate_to_author"


def test_run_writes_the_validated_patch(repo: Path, tmp_path: Path) -> None:
    # M13.23 (#107): --output-patch persists the validated diff.
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    patch_file = tmp_path / "fix.patch"
    result = RUNNER.invoke(
        app,
        [
            "run", "--junit", str(junit), "--repo", str(repo), "--seed", "1",
            "--failing-command", f'"{sys.executable}" check.py',
            "--output-patch", str(patch_file), "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["patch_path"] == str(patch_file)
    assert "+    return 2" in patch_file.read_text(encoding="utf-8")


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


def test_run_maps_an_unexpected_error_to_exit_5(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # M13.37 (#121): an internal failure is code 5 with a terminal event.
    import importlib

    app_module = importlib.import_module("markov_ci.cli.app")

    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")

    def _boom(**_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "run_loop", _boom)
    result = RUNNER.invoke(
        app,
        ["run", "--junit", str(junit), "--repo", str(repo), "--seed", "1",
         "--failing-command", f'"{sys.executable}" check.py'],
    )
    assert result.exit_code == 5, result.stdout


def _config_with(tmp_path: Path, *, agent: str = "", telemetry: str = "") -> Path:
    from markov_ci.data import default_config_path

    text = default_config_path().read_text(encoding="utf-8")
    if agent:
        text = text.replace("  adapter: simulated\n", f"  adapter: {agent}\n")
    if telemetry:
        text = text.replace("  sink: file\n", f"  sink: {telemetry}\n")
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_run_maps_a_harness_error_to_exit_1(repo: Path, tmp_path: Path) -> None:
    # M13.22/M13.37: a harness that cannot start → a2 + terminal event.
    config = _config_with(tmp_path, agent="harness").read_text(encoding="utf-8")
    config = config.replace(
        "  adapter: harness\n",
        "  adapter: harness\n  harness:\n    command_template: 'no-such-harness-xyz %PROMPT%'\n",
    )
    path = tmp_path / "harness.yaml"
    path.write_text(config, encoding="utf-8")
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app, ["run", str(path), "--junit", str(junit), "--repo", str(repo)],
    )
    assert result.exit_code == 1, result.stdout


def test_run_with_publish_and_no_remote_reports_no_branch(
    repo: Path, tmp_path: Path,
) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        ["run", "--junit", str(junit), "--repo", str(repo), "--seed", "1",
         "--failing-command", f'"{sys.executable}" check.py', "--publish", "--json"],
    )
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["patch_branch"] is None


def test_run_with_sink_none_writes_no_events(repo: Path, tmp_path: Path) -> None:
    config = _config_with(tmp_path, telemetry="none")
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        ["run", str(config), "--junit", str(junit), "--repo", str(repo), "--seed", "1",
         "--failing-command", f'"{sys.executable}" check.py', "--json"],
    )
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["events_path"] is None


def test_run_rejects_an_unsupported_adapter(repo: Path, tmp_path: Path) -> None:
    junit = tmp_path / "report.xml"
    junit.write_text(JUNIT, encoding="utf-8")
    result = RUNNER.invoke(
        app,
        ["run", "--junit", str(junit), "--repo", str(repo), "--adapter", "bogus"],
    )
    assert result.exit_code == 4, result.stdout


def test_recompute_with_a_config_prior(repo: Path, tmp_path: Path) -> None:
    from markov_ci.data import default_config_path

    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps({
            "event": "transition", "adapter": "harness", "failure_category": "c",
            "from_state": "s2_agent_reasoning#1", "to_state": "s3_sandbox_validation#1",
            "synthetic": False,
        }) + "\n",
        encoding="utf-8",
    )
    result = RUNNER.invoke(
        app, ["recompute", str(events), "--config", str(default_config_path()), "--json"],
    )
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)


def test_module_entry_point_runs(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[2] / "src"
    completed = subprocess.run(
        [sys.executable, "-m", "markov_ci", "--help"],
        capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(src)},
    )
    assert completed.returncode == 0
    assert "markov" in completed.stdout.lower() or "Usage" in completed.stdout
