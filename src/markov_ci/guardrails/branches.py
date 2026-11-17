"""Patch branch isolation (docs/spec/0005-guardrails.md §3–4).

Agent patches land on ``ai-fix/pr-<n>`` (or ``ai-fix/local-<run_id>``), never the PR
branch and never ``main``. There is deliberately **no force-push path anywhere** in
this module: concurrent runs for one PR get distinct branch names rather than
clobbering each other, and `a1` never merges.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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
