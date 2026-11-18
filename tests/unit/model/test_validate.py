"""M1.4 (#10) — matrix validation (docs/spec/0002-matrix-assembly.md §1.4)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from markov_ci.model.assemble import Chain
from markov_ci.model.validate import Finding, ValidationResult, validate


def _chain(transient: list[str], absorbing: list[str], rows: dict[str, dict[str, float]]) -> Chain:
    states = tuple(transient + absorbing)
    index = {state_id: position for position, state_id in enumerate(states)}
    matrix = np.zeros((len(states), len(states)), dtype=np.float64)
    for source, targets in rows.items():
        for target, probability in targets.items():
            matrix[index[source], index[target]] = probability
    t = len(transient)
    return Chain(
        states=states,
        transient=tuple(transient),
        absorbing=tuple(absorbing),
        index=index,
        P=matrix,
        Q=matrix[:t, :t],
        R=matrix[:t, t:],
    )


def _valid_chain() -> Chain:
    return _chain(
        ["s0", "s1"],
        ["a1"],
        {
            "s0": {"s1": 0.5, "a1": 0.5},
            "s1": {"s0": 0.25, "a1": 0.75},
            "a1": {"a1": 1.0},
        },
    )


def test_valid_chain_reports_ok_with_no_findings() -> None:
    result = validate(_valid_chain())
    assert result.ok is True
    assert result.findings == ()


def test_row_that_does_not_sum_to_one_is_flagged_with_the_state() -> None:
    chain = _chain(
        ["s0", "s1"],
        ["a1"],
        {
            "s0": {"s1": 0.2, "a1": 0.2},  # sums to 0.4
            "s1": {"a1": 1.0},
            "a1": {"a1": 1.0},
        },
    )
    result = validate(chain)
    assert result.ok is False
    codes = {(f.code, f.state) for f in result.findings}
    assert ("row_sum", "s0") in codes


def test_absorbing_row_that_is_not_identity_is_flagged() -> None:
    chain = _chain(
        ["s0"],
        ["a1"],
        {"s0": {"a1": 0.0, "s0": 1.0}, "a1": {"a1": 0.5, "s0": 0.5}},
    )
    result = validate(chain)
    assert result.ok is False
    codes = {f.code for f in result.findings}
    assert "absorbing_identity" in codes


def test_transient_that_cannot_reach_absorption_is_flagged() -> None:
    # s0 <-> s1 loop with no exit; a1 is unreachable
    chain = _chain(
        ["s0", "s1"],
        ["a1"],
        {
            "s0": {"s1": 1.0},
            "s1": {"s0": 1.0},
            "a1": {"a1": 1.0},
        },
    )
    result = validate(chain)
    assert result.ok is False
    unreachable = {f.state for f in result.findings if f.code == "unreachable_absorption"}
    assert unreachable == {"s0", "s1"}


def test_findings_are_deterministic_and_ordered() -> None:
    chain = _chain(
        ["s0", "s1"],
        ["a1"],
        {"s0": {"s1": 0.0}, "s1": {"s0": 0.0}, "a1": {"a1": 1.0}},
    )
    first = validate(chain)
    second = validate(chain)
    assert first == second


def test_result_is_machine_readable() -> None:
    chain = _chain(
        ["s0", "s1"],
        ["a1"],
        {"s0": {"s1": 0.1}, "s1": {"s0": 0.1}, "a1": {"a1": 1.0}},
    )
    payload = validate(chain).as_dict()
    assert payload["ok"] is False
    assert isinstance(payload["findings"], list)
    assert {"code", "message", "state"} <= set(payload["findings"][0])


def test_validation_does_not_mutate_the_matrix() -> None:
    chain = _chain(
        ["s0", "s1"],
        ["a1"],
        {"s0": {"s1": 0.2, "a1": 0.2}, "s1": {"a1": 1.0}, "a1": {"a1": 1.0}},
    )
    before = chain.P.copy()
    validate(chain)
    assert np.array_equal(before, chain.P)


def test_finding_and_result_are_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        Finding(code="x", message="y").code = "z"  # type: ignore[misc]
    assert ValidationResult(ok=True, findings=()).ok is True


def test_probability_outside_the_unit_interval_is_flagged() -> None:
    # M13.30 (#114): every matrix entry must lie in [0, 1].
    chain = _chain(
        ["s0"],
        ["a1"],
        {"s0": {"a1": 1.5}, "a1": {"a1": 1.0}},
    )
    findings = validate(chain).findings
    assert any(f.code == "probability_range" for f in findings)
