"""markov_ci.triage — deterministic failure classification."""

from __future__ import annotations

from markov_ci.triage.classify import FailureCategory, TriageReport, classify
from markov_ci.triage.junit import JUnitReport, TestFailure, parse_junit

__all__ = [
    "FailureCategory",
    "JUnitReport",
    "TestFailure",
    "TriageReport",
    "classify",
    "parse_junit",
]

