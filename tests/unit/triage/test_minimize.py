"""M3.3 (#21) — log minimizer (docs/spec/0010-triage.md §3)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from markov_ci.triage.junit import TestFailure
from markov_ci.triage.minimize import MAX_LINES, MinimizedContext, minimize

FAILURE = TestFailure(name="test_checkout", message="AssertionError: 1 != 2", kind="failure")


def test_empty_input_is_minimal() -> None:
    result = minimize([])
    assert isinstance(result, MinimizedContext)
    assert result.line_count <= MAX_LINES


def test_failing_block_is_included() -> None:
    result = minimize([FAILURE])
    assert "test_checkout" in result.text
    assert "AssertionError: 1 != 2" in result.text


def test_failing_block_survives_truncation() -> None:
    huge_logs = "\n".join(f"line {i}" for i in range(5000))
    result = minimize([FAILURE], logs=huge_logs)
    assert result.truncated is True
    assert "test_checkout" in result.text


def test_line_count_never_exceeds_the_cap() -> None:
    huge_logs = "\n".join(f"line {i}" for i in range(5000))
    result = minimize([FAILURE], logs=huge_logs, diff="+a\n-b\n" * 100)
    assert result.line_count == MAX_LINES


def test_diff_is_included() -> None:
    result = minimize([FAILURE], diff="--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new")
    assert "+new" in result.text


def test_secrets_are_scrubbed() -> None:
    logs = (
        "token=ghp_abcdefghijklmnopqrstuvwxyz0123\n"
        "AWS key AKIAIOSFODNN7EXAMPLE\n"
        "password: hunter2\n"
    )
    result = minimize([FAILURE], logs=logs)
    assert "ghp_abcdefghijklmnopqrstuvwxyz0123" not in result.text
    assert "AKIAIOSFODNN7EXAMPLE" not in result.text
    assert "hunter2" not in result.text
    assert result.redactions >= 3


def test_scrubbing_does_not_mangle_ordinary_text() -> None:
    result = minimize([FAILURE], logs="the assertion failed because 1 != 2")
    assert "the assertion failed because 1 != 2" in result.text
    assert result.redactions == 0


def test_is_deterministic() -> None:
    logs = "x\ny\nz"
    assert minimize([FAILURE], logs=logs) == minimize([FAILURE], logs=logs)


@given(logs=st.text(min_size=0, max_size=20000))
@settings(max_examples=100, deadline=None)
def test_property_line_cap_holds_for_arbitrary_logs(logs: str) -> None:
    result = minimize([FAILURE], logs=logs)
    assert result.line_count <= MAX_LINES


def test_rejects_non_positive_cap() -> None:
    with pytest.raises(ValueError, match="max_lines"):
        minimize([FAILURE], max_lines=0)
