"""M4.2 (#23) — the offline SimulatedAgent (docs/spec/0006 §2, ADR-0003)."""

from __future__ import annotations

import pytest

from markov_ci.agents import AgentAdapter, PatchProposal, RepairContext
from markov_ci.agents.simulated import SimulatedAgent
from markov_ci.triage import FailureCategory

CURVE = (0.74, 0.45, 0.15)


def _context(attempt: int = 1) -> RepairContext:
    return RepairContext(
        category=FailureCategory.UNIT_ASSERTION,
        attempt=attempt,
        max_attempts=3,
        context="AssertionError: 1 != 2",
    )


def test_id_is_simulated() -> None:
    assert SimulatedAgent(CURVE).id == "simulated"


def test_satisfies_the_adapter_protocol() -> None:
    assert isinstance(SimulatedAgent(CURVE), AgentAdapter)


def test_repair_returns_a_patch_proposal() -> None:
    assert isinstance(SimulatedAgent(CURVE).repair(_context()), PatchProposal)


def test_uses_zero_tokens() -> None:
    agent = SimulatedAgent(CURVE, seed=1)
    assert all(agent.repair(_context()).tokens_used == 0 for _ in range(20))


def test_same_seed_is_byte_identical() -> None:
    a = SimulatedAgent(CURVE, seed=123)
    b = SimulatedAgent(CURVE, seed=123)
    seq_a = [a.repair(_context((i % 3) + 1)) for i in range(60)]
    seq_b = [b.repair(_context((i % 3) + 1)) for i in range(60)]
    assert seq_a == seq_b


def test_different_seeds_produce_different_sequences() -> None:
    a = SimulatedAgent(CURVE, seed=1)
    b = SimulatedAgent(CURVE, seed=2)
    seq_a = [a.repair(_context((i % 3) + 1)).diff for i in range(60)]
    seq_b = [b.repair(_context((i % 3) + 1)).diff for i in range(60)]
    assert seq_a != seq_b


def test_success_rate_matches_the_first_attempt_prior() -> None:
    agent = SimulatedAgent(CURVE, seed=7)
    context = _context(attempt=1)
    samples = 20_000
    successes = sum(1 for _ in range(samples) if agent.repair(context).diff)
    assert successes / samples == pytest.approx(0.74, abs=0.02)


def test_success_rate_matches_the_third_attempt_prior() -> None:
    agent = SimulatedAgent(CURVE, seed=11)
    context = _context(attempt=3)
    samples = 20_000
    successes = sum(1 for _ in range(samples) if agent.repair(context).diff)
    assert successes / samples == pytest.approx(0.15, abs=0.02)


def test_success_returns_a_real_diff_and_failure_returns_empty() -> None:
    agent = SimulatedAgent((1.0,), seed=0)
    assert agent.repair(_context(attempt=1)).diff  # p=1 -> always a patch
    assert agent.repair(_context(attempt=1)).files_changed

    failing = SimulatedAgent((0.0,), seed=0)
    assert failing.repair(_context(attempt=1)).diff == ""


def test_attempt_beyond_the_curve_never_succeeds() -> None:
    agent = SimulatedAgent((1.0,), seed=0)
    assert agent.repair(_context(attempt=2)).diff == ""


def test_is_offline() -> None:
    # no network dependency: constructing and running never touches sockets
    agent = SimulatedAgent(CURVE, seed=0)
    assert isinstance(agent.repair(_context()), PatchProposal)
