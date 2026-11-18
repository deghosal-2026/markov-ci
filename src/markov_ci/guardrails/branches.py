"""Patch branch isolation (docs/spec/0005-guardrails.md §3–4).

Agent patches land on ``ai-fix/pr-<n>`` (or ``ai-fix/local-<run_id>``), never the PR
branch and never ``main``. There is deliberately **no force-push path anywhere** in
this module: concurrent runs for one PR get distinct branch names rather than
clobbering each other, and `a1` never merges.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_PREFIX = "ai-fix"
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


@dataclass(frozen=True, slots=True)
class PatchBranch:
    """A resolved, isolated patch branch."""

    name: str
    pr_number: int | None
    run_id: str | None


def _sanitise(run_id: str) -> str:
    cleaned = _UNSAFE.sub("-", run_id).strip("-")
    return cleaned[:8] or "run"


def patch_branch(*, pr_number: int | None = None, run_id: str | None = None) -> PatchBranch:
    """Resolve the isolated patch branch for a run.

    Passing a ``run_id`` disambiguates concurrent runs on the same PR.
    """
    if pr_number is not None:
        suffix = f"-{_sanitise(run_id)}" if run_id else ""
        name = f"{_PREFIX}/pr-{pr_number}{suffix}"
    elif run_id is not None:
        name = f"{_PREFIX}/local-{_sanitise(run_id)}"
    else:
        raise ValueError("patch_branch requires either pr_number or run_id")
    return PatchBranch(name=name, pr_number=pr_number, run_id=run_id)


def push_commands(branch: str, remote: str = "origin") -> tuple[tuple[str, ...], ...]:
    """The exact git commands that publish a patch branch — never force-pushing."""
    return (
        ("git", "checkout", "-b", branch),
        ("git", "add", "-A"),
        ("git", "commit", "-m", "chore(ci-agent): automated fix"),
        ("git", "push", "-u", remote, branch),
    )


def publish_commands(
    branch: str, paths: Sequence[str], *, base: str, remote: str = "origin",
) -> tuple[tuple[str, ...], ...]:
    """The exact commands that publish **only the validated paths** (M13.24).

    Never ``git add -A`` (a stray file must not ride along) and never a force push.
    """
    return (
        ("git", "checkout", "-b", branch, base),
        ("git", "add", "--", *paths),
        ("git", "commit", "-m", "chore(ci-agent): automated fix"),
        ("git", "push", "-u", remote, branch),
    )


def publish_patch(
    repo: str | Path,
    *,
    branch: str,
    diff: str,
    paths: Sequence[str],
    base: str = "HEAD",
    remote: str = "origin",
) -> str | None:
    """Apply exactly ``diff`` to ``branch`` off ``base`` and push it (M13.24).

    Returns the branch name only after a successful push; ``None`` on any failure.
    Commits only ``paths``; asserts git's staged set equals them; never forces.
    """
    expected = set(paths)

    def _git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False,
        )

    if _git("checkout", "-b", branch, base).returncode != 0:
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False) as handle:
        handle.write(diff)
        patch_file = handle.name
    try:
        if _git("apply", patch_file).returncode != 0:
            return None
    finally:
        os.unlink(patch_file)
    if not paths or _git("add", "--", *paths).returncode != 0:
        return None
    staged = set(_git("diff", "--cached", "--name-only").stdout.split())
    if staged != expected:
        return None
    if _git("commit", "-m", "chore(ci-agent): automated fix").returncode != 0:
        return None
    if _git("push", "-u", remote, branch).returncode != 0:
        return None
    return branch
