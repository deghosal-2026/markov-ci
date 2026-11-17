"""Sandbox apply-and-test (docs/spec/0011-engine-runtime.md §2).

A patch is applied in a disposable git worktree and reverted by simply discarding
the worktree — the PR branch and ``main`` are never touched. The worktree is
removed in a ``finally`` block, so cleanup happens even if the test command
explodes.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """The result of applying and testing a patch in isolation."""

    applied: bool
    passed: bool
    output: str


class Sandbox:
    """A disposable worktree rooted at a temporary directory."""

    def __init__(self, repo: str | Path, *, root: str | Path | None = None) -> None:
        self._repo = Path(repo).resolve()
        self._root = (
            Path(root) if root is not None
            else Path(tempfile.mkdtemp(prefix="markov-sandbox-"))
        )
        self._root.mkdir(parents=True, exist_ok=True)

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(cwd or self._repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def apply_and_test(
        self,
        diff: str,
        command: Sequence[str],
        *,
        timeout: int = 600,
    ) -> SandboxResult:
        """Apply ``diff`` in a fresh worktree and run ``command`` there."""
        worktree = self._root / f"wt-{uuid4().hex[:8]}"
        try:
            add = self._git("worktree", "add", "--detach", str(worktree), "HEAD")
            if add.returncode != 0:
                return SandboxResult(False, False, f"worktree add failed: {add.stderr}")

            patch_file = self._root / "patch.diff"
            patch_file.write_text(diff, encoding="utf-8")
            apply = self._git("apply", str(patch_file), cwd=worktree)
            if apply.returncode != 0:
                return SandboxResult(False, False, f"patch did not apply: {apply.stderr}")

            try:
                completed = subprocess.run(
                    list(command),
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(True, False, "test command timed out")
            output = completed.stdout + completed.stderr
            return SandboxResult(True, completed.returncode == 0, output)
        finally:
            self._git("worktree", "remove", "--force", str(worktree))
            shutil.rmtree(worktree, ignore_errors=True)
            self._git("worktree", "prune")

    def close(self) -> None:
        shutil.rmtree(self._root, ignore_errors=True)

    def __enter__(self) -> Sandbox:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
