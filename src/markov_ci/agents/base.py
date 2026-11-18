"""The agent adapter seam (docs/spec/0006-agent-adapters.md §1).

One thin protocol lets any agent run under governance while keeping the core free
of agent-specific assumptions. The engine never trusts an adapter: every
`PatchProposal` still has to clear the guardrails and worktree validation before any state
advances.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from markov_ci.triage import FailureCategory
from markov_ci.triage.minimize import MAX_LINES


@dataclass(frozen=True, slots=True)
class RepairContext:
    """Everything an adapter is given — deliberately bounded and secret-free.

    ``context`` must be the *minimized* log (spec 0010 §3); passing raw logs is a
    programming error and is rejected here.
    """

    category: FailureCategory
    attempt: int
    max_attempts: int
    context: str
    diff: str | None = None
    repo_rules: tuple[str, ...] = ()
    timeout: int | None = None

    def __post_init__(self) -> None:
        if self.attempt < 1:
            raise ValueError(f"attempt must be >= 1, got {self.attempt}")
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {self.max_attempts}")
        line_count = len(self.context.splitlines())
        if line_count > MAX_LINES:
            raise ValueError(
                f"repair context must be <= {MAX_LINES} lines, got {line_count}; "
                "pass the minimized log, not raw output",
            )


@dataclass(frozen=True, slots=True)
class PatchProposal:
    """A proposed fix produced by an adapter."""

    diff: str
    rationale: str
    tokens_used: int | None = None
    files_changed: tuple[str, ...] = ()


@runtime_checkable
class AgentAdapter(Protocol):
    """An agent that can propose a patch for a classified failure."""

    id: str

    def repair(self, ctx: RepairContext) -> PatchProposal: ...
