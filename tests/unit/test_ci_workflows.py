"""M0.4 — CI workflows exist and enforce the gate on every PR (F14)."""

from __future__ import annotations

from pathlib import Path

WF = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _read(name: str) -> str:
    return (WF / name).read_text(encoding="utf-8")


def test_workflow_files_exist() -> None:
    for name in ("ci.yml", "integration.yml", "cancel-closed-pr.yml"):
        assert (WF / name).is_file(), f"missing workflow {name}"


def test_ci_triggers_on_pull_request() -> None:
    assert "pull_request" in _read("ci.yml")


def test_ci_runs_the_full_gate() -> None:
    text = _read("ci.yml")
    for tool in ("ruff", "mypy", "pytest"):
        assert tool in text, f"{tool} not run in ci.yml"


def test_ci_covers_supported_python_versions() -> None:
    text = _read("ci.yml")
    for version in ("3.11", "3.12", "3.13"):
        assert version in text, f"python {version} missing from matrix"


def test_ci_cancels_superseded_runs() -> None:
    assert "cancel-in-progress: true" in _read("ci.yml")


def test_ci_gate_has_no_secrets_dependency() -> None:
    # lint/typecheck/unit must run on fork PRs too.
    assert "secrets." not in _read("ci.yml")


def test_integration_workflow_runs_integration_tests() -> None:
    assert "tests/integration" in _read("integration.yml")


def test_cancel_workflow_targets_closed_prs() -> None:
    text = _read("cancel-closed-pr.yml")
    assert "closed" in text and "cancelWorkflowRun" in text
