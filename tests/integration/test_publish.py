"""M13.24 (#108) — opt-in publish to a fresh patch branch (spec 0005 §3–4)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from markov_ci.guardrails.branches import publish_commands, publish_patch

DIFF = (
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1 +1 @@\n"
    "-VALUE = 1\n"
    "+VALUE = 2\n"
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
    )


def test_publish_commands_never_add_all() -> None:
    commands = publish_commands("ai-fix/pr-1", ["src/app.py"], base="HEAD")
    assert ("git", "add", "-A") not in commands
    assert ("git", "add", "--", "src/app.py") in commands


def test_publish_commands_never_force() -> None:
    for command in publish_commands("ai-fix/pr-1", ["src/app.py"], base="HEAD"):
        assert "--force" not in command
        assert "-f" not in command


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "branch", "-M", "main")  # pin the branch name; CI's git may default to master
    _git(path, "config", "user.email", "t@e.com")
    _git(path, "config", "user.name", "T")
    (path / "src").mkdir()
    (path / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "base")
    _git(path, "remote", "add", "origin", str(remote))
    _git(path, "push", "-qu", "origin", "HEAD:main")
    return path


def test_publish_creates_the_branch_with_the_exact_diff(repo: Path) -> None:
    branch = publish_patch(
        repo, branch="ai-fix/pr-1", diff=DIFF, paths=["src/app.py"],
    )
    assert branch == "ai-fix/pr-1"
    branches = subprocess.run(
        ["git", "-C", str(repo), "branch", "-a"], capture_output=True, text=True, check=True,
    ).stdout
    assert "ai-fix/pr-1" in branches
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "main", "ai-fix/pr-1"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "-VALUE = 1" in diff
    assert "+VALUE = 2" in diff


def test_publish_commits_only_the_validated_paths(repo: Path) -> None:
    # a stray untracked file in the workspace must not ride along
    (repo / "stray.txt").write_text("noise\n", encoding="utf-8")
    publish_patch(repo, branch="ai-fix/pr-2", diff=DIFF, paths=["src/app.py"])
    committed = subprocess.run(
        ["git", "-C", str(repo), "show", "--name-only", "--pretty=format:", "ai-fix/pr-2"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert committed == ["src/app.py"]


def test_publish_returns_none_when_the_push_fails(repo: Path) -> None:
    _git(repo, "remote", "set-url", "origin", str(repo.parent / "nope.git"))
    assert publish_patch(repo, branch="ai-fix/pr-3", diff=DIFF, paths=["src/app.py"]) is None


def test_publish_returns_none_for_a_bad_diff(repo: Path) -> None:
    assert publish_patch(
        repo, branch="ai-fix/pr-bad", diff="not a diff at all", paths=["src/app.py"],
    ) is None


def test_publish_returns_none_for_no_paths(repo: Path) -> None:
    assert publish_patch(
        repo, branch="ai-fix/pr-none", diff=DIFF, paths=[],
    ) is None


def test_publish_returns_none_when_the_branch_already_exists(repo: Path) -> None:
    assert publish_patch(repo, branch="ai-fix/pr-dup", diff=DIFF, paths=["src/app.py"])
    # the branch now exists, so the checkout -b fails
    assert publish_patch(repo, branch="ai-fix/pr-dup", diff=DIFF, paths=["src/app.py"]) is None


def test_publish_returns_none_when_the_staged_set_differs(repo: Path) -> None:
    # the diff touches src/app.py but we claim only README.md
    assert publish_patch(
        repo, branch="ai-fix/pr-mismatch", diff=DIFF, paths=["README.md"],
    ) is None
