"""M10.8 — the release security & supply-chain gate is wired into CI (#60)."""

from __future__ import annotations

from pathlib import Path

WF = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _read(name: str) -> str:
    return (WF / name).read_text(encoding="utf-8")


def test_security_workflow_exists() -> None:
    assert (WF / "security.yml").is_file()


def test_scans_git_history_for_secrets() -> None:
    text = _read("security.yml")
    lowered = text.lower()
    assert "trufflehog" in lowered
    assert "gitleaks" in lowered
    # full history is required to catch secrets in old commits
    assert "fetch-depth: 0" in text


def test_dependency_audit_and_sast_present() -> None:
    lowered = _read("security.yml").lower()
    assert "pip-audit" in lowered
    assert "bandit" in lowered


def test_runs_on_pr_schedule_and_main() -> None:
    text = _read("security.yml")
    assert "pull_request" in text
    assert "schedule" in text
    assert "push" in text
