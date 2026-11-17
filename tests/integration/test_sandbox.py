"""M6.3 (#31) — sandbox apply-and-test (docs/spec/0011-engine-runtime.md §2).

These are integration tests: they drive a real (tiny) git repository through the
worktree lifecycle.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from markov_ci.engine.sandbox import Sandbox, SandboxResult

GOOD_DIFF = """\
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""

BAD_DIFF = """\
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 3
"""

MALFORMED = "this is not a diff at all\n"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (path / "check.py").write_text(
        "import app\nassert app.VALUE == 2, 'not fixed'\n",
        encoding="utf-8",
    )
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "init")
    return path


def _test_command() -> list[str]:
    return [sys.executable, "check.py"]


def test_good_patch_applies_and_passes(repo: Path, tmp_path: Path) -> None:
    with Sandbox(repo, root=tmp_path / "sandbox") as sandbox:
        result = sandbox.apply_and_test(GOOD_DIFF, _test_command())
    assert isinstance(result, SandboxResult)
    assert result.applied is True
    assert result.passed is True


def test_bad_patch_applies_but_fails(repo: Path, tmp_path: Path) -> None:
    with Sandbox(repo, root=tmp_path / "sandbox") as sandbox:
        result = sandbox.apply_and_test(BAD_DIFF, _test_command())
    assert result.applied is True
    assert result.passed is False


def test_malformed_patch_does_not_apply(repo: Path, tmp_path: Path) -> None:
    with Sandbox(repo, root=tmp_path / "sandbox") as sandbox:
        result = sandbox.apply_and_test(MALFORMED, _test_command())
    assert result.applied is False
    assert result.passed is False


def test_the_repository_is_never_modified(repo: Path, tmp_path: Path) -> None:
    with Sandbox(repo, root=tmp_path / "sandbox") as sandbox:
        sandbox.apply_and_test(GOOD_DIFF, _test_command())
    assert (repo / "app.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    )
    assert status.stdout.strip() == ""


def test_worktrees_are_cleaned_up(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "sandbox"
    with Sandbox(repo, root=root) as sandbox:
        sandbox.apply_and_test(GOOD_DIFF, _test_command())
    assert not any(root.glob("wt-*"))
    listing = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        check=True, capture_output=True, text=True,
    )
    assert "wt-" not in listing.stdout


def test_cleanup_happens_even_when_the_test_command_explodes(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "sandbox"
    sandbox = Sandbox(repo, root=root)
    result = sandbox.apply_and_test(GOOD_DIFF, [sys.executable, "-c", "import sys; sys.exit(7)"])
    sandbox.close()
    assert result.passed is False
    assert not any(root.glob("wt-*"))


def test_close_removes_the_root(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "sandbox"
    sandbox = Sandbox(repo, root=root)
    sandbox.close()
    assert not root.exists() or not any(root.iterdir())


def test_python_is_not_needed_for_marking() -> None:
    # sanity: the fixture's interpreter exists
    assert shutil.which(sys.executable) or Path(sys.executable).exists()
