"""M3.1 (#19) — JUnit XML parser (docs/spec/0010-triage.md §1)."""

from __future__ import annotations

from markov_ci.triage.junit import JUnitReport, TestFailure, parse_junit

GOOD = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="unit">
    <testcase classname="pkg.mod" name="test_a">
      <failure message="boom" type="AssertionError">trace a</failure>
    </testcase>
    <testcase classname="pkg.mod" name="test_b">
      <error message="kaboom" type="TypeError">trace b</error>
    </testcase>
    <testcase classname="pkg.mod" name="test_c">
      <skipped message="skip me"/>
    </testcase>
    <testcase classname="pkg.mod" name="test_d"/>
  </testsuite>
</testsuites>
"""

NAMESPACED = """<?xml version="1.0"?>
<testsuites xmlns="urn:junit">
  <testsuite>
    <testcase name="test_ns">
      <failure message="ns boom" type="AssertionError"/>
    </testcase>
  </testsuite>
</testsuites>
"""

MALFORMED = (
    "<testsuites>\n"
    '  <testcase name="test_broken">'
    '<failure message="raw boom" type="AssertionError">trace</failure></testcase>\n'
)


def test_parses_failure_error_and_skipped() -> None:
    report = parse_junit(GOOD)
    kinds = [failure.kind for failure in report.failures]
    assert kinds == ["failure", "error", "skipped"]


def test_skipped_is_included() -> None:
    assert any(failure.kind == "skipped" for failure in parse_junit(GOOD).failures)


def test_extracts_name_message_and_kind() -> None:
    first = parse_junit(GOOD).failures[0]
    assert first == TestFailure(name="test_a", message="boom", kind="failure")


def test_error_message_and_kind() -> None:
    error = next(f for f in parse_junit(GOOD).failures if f.kind == "error")
    assert error.name == "test_b"
    assert error.message == "kaboom"


def test_passing_tests_are_excluded() -> None:
    names = {failure.name for failure in parse_junit(GOOD).failures}
    assert "test_d" not in names


def test_no_failures_reports_empty() -> None:
    report = parse_junit("<testsuites><testsuite><testcase name='x'/></testsuite></testsuites>")
    assert report.failures == ()
    assert report.warnings == ()


def test_namespaced_xml_is_handled() -> None:
    report = parse_junit(NAMESPACED)
    assert [f.name for f in report.failures] == ["test_ns"]
    assert report.failures[0].message == "ns boom"


def test_malformed_xml_does_not_crash_and_warns() -> None:
    report = parse_junit(MALFORMED)
    assert isinstance(report, JUnitReport)
    assert report.warnings  # a warning is recorded
    # best-effort recovery still finds the failure
    assert [f.name for f in report.failures] == ["test_broken"]
    assert report.failures[0].message == "raw boom"


def test_empty_input_is_empty_and_warns() -> None:
    report = parse_junit("")
    assert report.failures == ()
    assert report.warnings


def test_is_deterministic() -> None:
    assert parse_junit(GOOD) == parse_junit(GOOD)
