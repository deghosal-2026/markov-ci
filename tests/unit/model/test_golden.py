"""M1.7 (#13) — the worked-example golden fixture (docs/explanations/markov-model.md §5).

The default pipeline caps at `max_attempts = 3`, which truncates the agent loop:
P(a1 | s2) is ≈ 0.72 for the shipped default and approaches the uncapped limit
0.729 as attempts grow. P(a1 | s0) ≈ 0.92 either way. These numbers are asserted
here and must not drift from the docs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from markov_ci.model import (
    State,
    StateSpace,
    StateType,
    TransitionEdge,
    absorption,
    assemble,
    augment,
)

ROOT = Path(__file__).resolve().parents[3]

GOLDEN_A1_GIVEN_S0 = 0.92
GOLDEN_A1_GIVEN_S2_DEFAULT = 0.72
GOLDEN_A1_GIVEN_S2_UNCAPPED = 0.729

EDGES = (
    TransitionEdge(source="s0", target="a1"),
    TransitionEdge(source="s0", target="s1"),
    TransitionEdge(source="s1", target="s2"),
    TransitionEdge(source="s1", target="a2"),
    TransitionEdge(source="s2", target="s3"),
    TransitionEdge(source="s3", target="s4"),
    TransitionEdge(source="s3", target="s2", per_attempt=True),
    TransitionEdge(source="s3", target="a2"),
    TransitionEdge(source="s4", target="a1"),
    TransitionEdge(source="s4", target="a2"),
)


def _space() -> StateSpace:
    return StateSpace.of(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="s1", type=StateType.TRANSIENT),
        State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s3", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s4", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
        State(id="a2", type=StateType.ABSORBING),
    )


def _a1_probabilities(max_attempts: int) -> tuple[float, float]:
    success = (0.95,) * max_attempts
    weights = {
        ("s0", "a1"): 0.82,
        ("s0", "s1"): 0.18,
        ("s1", "s2"): 0.75,
        ("s1", "a2"): 0.25,
        ("s2", "s3"): lambda attempt: success[attempt - 1],
        ("s3", "s4"): 0.65,
        ("s3", "s2"): 0.25,
        ("s3", "a2"): 0.10,
        ("s4", "a1"): 0.90,
        ("s4", "a2"): 0.10,
    }
    chain = assemble(augment(_space(), EDGES, max_attempts=max_attempts), weights, sink="a2")
    b = absorption(chain)
    given_s0 = float(b[chain.transient.index("s0"), chain.absorbing.index("a1")])
    given_s2 = float(b[chain.transient.index("s2#1"), chain.absorbing.index("a1")])
    return given_s0, given_s2


def test_default_config_matches_the_golden_numbers() -> None:
    given_s0, given_s2 = _a1_probabilities(3)
    assert given_s0 == pytest.approx(GOLDEN_A1_GIVEN_S0, abs=0.01)
    assert given_s2 == pytest.approx(GOLDEN_A1_GIVEN_S2_DEFAULT, abs=0.01)


def test_loop_truncation_converges_to_the_uncapped_limit() -> None:
    _, given_s2 = _a1_probabilities(12)
    assert given_s2 == pytest.approx(GOLDEN_A1_GIVEN_S2_UNCAPPED, abs=0.001)


def test_docs_quote_the_golden_numbers() -> None:
    quick_start = (ROOT / "docs" / "quick-start.md").read_text(encoding="utf-8")
    assert "0.92" in quick_start
    assert "0.72" in quick_start
    markov = (ROOT / "docs" / "explanations" / "markov-model.md").read_text(encoding="utf-8")
    assert "0.729" in markov  # the uncapped limit is still documented
