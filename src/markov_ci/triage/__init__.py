"""markov_ci.triage — deterministic failure classification."""

from __future__ import annotations

from markov_ci.triage.classify import FailureCategory, TriageReport, classify
from markov_ci.triage.junit import JUnitReport, TestFailure, parse_junit
from markov_ci.triage.minimize import MAX_LINES, MinimizedContext, minimize

__all__ = [
    "MAX_LINES",
    "FailureCategory",
    "JUnitReport",
    "MinimizedContext",
    "TestFailure",
    "TriageReport",
    "classify",
    "minimize",
    "parse_junit",
]

