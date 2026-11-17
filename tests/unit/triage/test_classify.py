"""M3.2 (#20) — failure category classification (docs/spec/0010-triage.md §2, §4)."""

from __future__ import annotations

import pytest

from markov_ci.triage.classify import FailureCategory, TriageReport, classify
from markov_ci.triage.junit import TestFailure


def _failure(message: str, name: str = "test_x", kind: str = "failure") -> TestFailure:
    return TestFailure(name=name, message=message, kind=kind)


def test_infra_timeout_is_detected_and_not_agent_eligible() -> None:
    report = classify([_failure("TimeoutError: request timed out")])
    assert report.category is FailureCategory.INFRA_TIMEOUT
    assert report.eligible is False


def test_connection_refused_is_infra_timeout() -> None:
    report = classify([_failure("ConnectionRefused: could not connect")])
    assert report.category is FailureCategory.INFRA_TIMEOUT
    assert report.eligible is False


def test_dependency_error_is_detected() -> None:
    report = classify([_failure("ERROR: Could not find a version that satisfies the requirement")])
    assert report.category is FailureCategory.DEPENDENCY_ERROR
    assert report.eligible is False


def test_lint_error_is_detected_and_eligible() -> None:
    report = classify([_failure("E501 line too long (101 > 100)")])
    assert report.category is FailureCategory.LINT_ERROR
    assert report.eligible is True


def test_type_mismatch_is_detected_and_eligible() -> None:
    report = classify([_failure("error: Incompatible type in mypy: expected int")])
    assert report.category is FailureCategory.TYPE_MISMATCH
    assert report.eligible is True


def test_unit_assertion_is_detected_and_eligible() -> None:
    report = classify([_failure("AssertionError: 1 != 2")])
    assert report.category is FailureCategory.UNIT_ASSERTION
    assert report.eligible is True


def test_unknown_is_not_eligible_by_default() -> None:
    report = classify([_failure("something inscrutable happened")])
    assert report.category is FailureCategory.UNKNOWN
    assert report.eligible is False


def test_unknown_can_be_opted_in() -> None:
    report = classify([_failure("something inscrutable happened")], allow_unknown=True)
    assert report.category is FailureCategory.UNKNOWN
    assert report.eligible is True


def test_logs_are_used_when_there_are_no_failures() -> None:
    report = classify([], logs="Traceback ... AssertionError: nope")
    assert report.category is FailureCategory.UNIT_ASSERTION


def test_matched_signatures_are_recorded() -> None:
    report = classify([_failure("TimeoutError: timed out")])
    assert report.matched
    assert all(isinstance(signature, str) for signature in report.matched)
    assert any("timeout" in signature for signature in report.matched)


def test_infra_takes_priority_over_assertion() -> None:
    report = classify([_failure("AssertionError raised after TimeoutError")])
    assert report.category is FailureCategory.INFRA_TIMEOUT


def test_report_reason_is_present() -> None:
    assert classify([_failure("AssertionError")]).reason
    assert classify([_failure("???")]).reason


def test_classification_is_deterministic() -> None:
    failures = [_failure("AssertionError: x")]
    assert classify(failures) == classify(failures)


def test_result_type() -> None:
    assert isinstance(classify([_failure("AssertionError")]), TriageReport)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("E501 line too long", FailureCategory.LINT_ERROR),
        ("F401 imported but unused", FailureCategory.LINT_ERROR),
        ("mypy: incompatible type", FailureCategory.TYPE_MISMATCH),
        ("AssertionError", FailureCategory.UNIT_ASSERTION),
    ],
)
def test_parametrised_signatures(message: str, expected: FailureCategory) -> None:
    assert classify([_failure(message)]).category is expected
