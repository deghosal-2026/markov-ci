"""M4.1 (#22) — the agent adapter seam (docs/spec/0006-agent-adapters.md §1)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from markov_ci.agents import AgentAdapter, PatchProposal, RepairContext
from markov_ci.triage import FailureCategory
from markov_ci.triage.minimize import MAX_LINES


class DummyAdapter:
    id = "dummy"

    def repair(self, ctx: RepairContext) -> PatchProposal:
        return PatchProposal(diff="", rationale="no-op")


class NotAnAdapter:
    id = "nope"


def _context(**overrides: object) -> RepairContext:
    values: dict[str, object] = {
        "category": FailureCategory.UNIT_ASSERTION,
        "attempt": 1,
        "max_attempts": 3,
        "context": "AssertionError: 1 != 2",
    }
    values.update(overrides)
    return RepairContext(**values)  # type: ignore[arg-type]


def test_conforming_adapter_satisfies_the_protocol() -> None:
    assert isinstance(DummyAdapter(), AgentAdapter)


def test_object_without_repair_is_not_an_adapter() -> None:
    assert not isinstance(NotAnAdapter(), AgentAdapter)


def test_repair_returns_a_patch_proposal() -> None:
    assert isinstance(DummyAdapter().repair(_context()), PatchProposal)


def test_repair_context_carries_only_the_category_and_attempt() -> None:
    context = _context()
    assert context.category is FailureCategory.UNIT_ASSERTION
    assert context.attempt == 1
    assert context.max_attempts == 3


def test_repair_context_rejects_oversized_logs() -> None:
    oversized = "\n".join(f"line {i}" for i in range(MAX_LINES + 1))
    with pytest.raises(ValueError, match="lines"):
        _context(context=oversized)


def test_repair_context_accepts_exactly_the_cap() -> None:
    at_cap = "\n".join(f"line {i}" for i in range(MAX_LINES))
    assert _context(context=at_cap).context


def test_attempt_must_be_positive() -> None:
    with pytest.raises(ValueError, match="attempt"):
        _context(attempt=0)


def test_max_attempts_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        _context(max_attempts=0)


def test_patch_proposal_defaults() -> None:
    proposal = PatchProposal(diff="--- a\n+++ b", rationale="fix")
    # M13.21 (#105): unknown usage is None, not a false zero.
    assert proposal.tokens_used is None
    assert proposal.files_changed == ()


def test_patch_proposal_is_frozen() -> None:
    proposal = PatchProposal(diff="", rationale="")
    with pytest.raises(FrozenInstanceError):
        proposal.diff = "x"  # type: ignore[misc]


def test_repair_context_is_frozen() -> None:
    context = _context()
    with pytest.raises(FrozenInstanceError):
        context.attempt = 2  # type: ignore[misc]
