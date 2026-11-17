"""M5.3 (#28) — patch branch isolation (docs/spec/0005-guardrails.md §3–4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from markov_ci.guardrails.branches import (
    PatchBranch,
    patch_branch,
    push_commands,
)

MODULE = Path(__file__).resolve().parents[3] / "src" / "markov_ci" / "guardrails" / "branches.py"


def test_branch_for_a_pull_request() -> None:
    assert patch_branch(pr_number=42).name == "ai-fix/pr-42"


def test_branch_for_a_local_run() -> None:
    assert patch_branch(run_id="abcdef12").name == "ai-fix/local-abcdef12"


def test_run_id_disambiguates_concurrent_runs_on_one_pr() -> None:
    first = patch_branch(pr_number=7, run_id="aaaaaaaa").name
    second = patch_branch(pr_number=7, run_id="bbbbbbbb").name
    assert first != second
    assert first.startswith("ai-fix/pr-7")
    assert second.startswith("ai-fix/pr-7")


def test_branch_name_is_deterministic() -> None:
    assert patch_branch(pr_number=7, run_id="zzzz") == patch_branch(pr_number=7, run_id="zzzz")


def test_requires_some_identity() -> None:
    with pytest.raises(ValueError, match="pr_number or run_id"):
        patch_branch()


def test_returns_a_patch_branch_record() -> None:
    branch = patch_branch(pr_number=5)
    assert isinstance(branch, PatchBranch)
    assert branch.name == "ai-fix/pr-5"
    assert branch.pr_number == 5


def test_run_id_is_sanitised() -> None:
    branch = patch_branch(run_id="a/b c!d")
    assert "/" not in branch.name.replace("ai-fix/", "")
    assert " " not in branch.name


def test_push_commands_never_force() -> None:
    commands = push_commands("ai-fix/pr-42")
    assert commands
    for command in commands:
        assert "--force" not in command
        assert "-f" not in command
    assert commands[-1][:2] == ("git", "push")


def test_target_branch_is_never_main_or_the_pr_branch() -> None:
    branch = patch_branch(pr_number=9)
    assert branch.name != "main"
    assert branch.name.startswith("ai-fix/")


def test_module_source_contains_no_force_push_path() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "--force" not in source
    assert "--force-with-lease" not in source
    assert "force=True" not in source
