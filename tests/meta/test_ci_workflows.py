"""M0.4 — CI workflows exist and enforce the gate on every PR (F14)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _yaml(name: str) -> Any:
    import yaml

    return yaml.safe_load(_read(name))


def test_ci_matrix_is_parsed_from_yaml_not_grepped() -> None:
    # M13.40 (#124): assert structure, not substrings.
    workflow = _yaml("ci.yml")
    matrix = workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"]
    assert matrix == ["3.11", "3.12", "3.13"]


def test_ci_coverage_flag_is_parsed_from_yaml() -> None:
    workflow = _yaml("ci.yml")
    runs = " ".join(
        step.get("run", "") for step in workflow["jobs"]["test"]["steps"]
    )
    assert "--cov-branch" in runs
    assert "--cov-fail-under=95" in runs


def test_release_tests_gate_the_build() -> None:
    workflow = _yaml("release.yml")
    needs = workflow["jobs"]["build"]["needs"]
    assert "gate" in needs and "test" in needs


def test_every_action_is_pinned_by_full_sha() -> None:
    # M13.35 (#119): every `uses:` is a 40-char commit SHA.
    import re

    for name in ("ci.yml", "release.yml", "security.yml", "integration.yml", "docs.yml"):
        workflow = _yaml(name)
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if not uses or uses.startswith("./"):
                    continue
                ref = uses.split("@", 1)[1].split()[0]
                assert re.fullmatch(r"[0-9a-f]{40}", ref), f"{name}: {uses} is not pinned"


def test_iac_linters_are_wired() -> None:
    text = _read("ci.yml")
    assert "actionlint" in text
    assert "hadolint" in text
