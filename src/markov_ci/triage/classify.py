"""Deterministic failure classification (docs/spec/0010-triage.md §2, §4).

Rule-based and deterministic — no randomness, no ML. Nothing reaches an agent
before this has run, and infrastructure or dependency failures are routed straight
to escalation so they never cost tokens.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from markov_ci.triage.junit import TestFailure


class FailureCategory(StrEnum):
    """The triage taxonomy."""

    LINT_ERROR = "lint_error"
    TYPE_MISMATCH = "type_mismatch"
    UNIT_ASSERTION = "unit_assertion"
    INFRA_TIMEOUT = "infra_timeout"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN = "unknown"


_AGENT_ELIGIBLE = frozenset(
    {
        FailureCategory.LINT_ERROR,
        FailureCategory.TYPE_MISMATCH,
        FailureCategory.UNIT_ASSERTION,
    },
)

# Ordered by priority; the first category with a matching signature wins.
_SIGNATURES: tuple[tuple[FailureCategory, tuple[str, ...]], ...] = (
    (
        FailureCategory.INFRA_TIMEOUT,
        (
            "timeouterror",
            "timeout expired",
            "timed out",
            "connectionrefused",
            "connection refused",
            "connection reset",
            "spot instance",
            "temporary failure in name resolution",
            "read timed out",
        ),
    ),
    (
        FailureCategory.DEPENDENCY_ERROR,
        (
            "could not find a version",
            "no matching distribution",
            "packagenotfounderror",
            "npm err",
            "dependency resolution",
            "failed to fetch",
            "registry 503",
            "503 service unavailable",
        ),
    ),
    (
        FailureCategory.TYPE_MISMATCH,
        (
            "mypy",
            "pyright",
            "incompatible type",
            "typeerror",
            "has no attribute",
        ),
    ),
    (
        FailureCategory.LINT_ERROR,
        (
            "flake8",
            "ruff",
            "prettier",
            "would reformat",
            "e501",
            "f401",
            "missing whitespace",
            "line too long",
        ),
    ),
    (
        FailureCategory.UNIT_ASSERTION,
        (
            "assertionerror",
            "assertion failed",
            "assert ",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class TriageReport:
    """The classification outcome and routing decision."""

    category: FailureCategory
    eligible: bool
    matched: tuple[str, ...]
    reason: str


def _collect_text(failures: Sequence[TestFailure], logs: str | None) -> str:
    parts: list[str] = []
    for failure in failures:
        parts.extend((failure.name, failure.message, failure.kind))
    if logs:
        parts.append(logs)
    return "\n".join(parts).lower()


def classify(
    failures: Sequence[TestFailure] = (),
    logs: str | None = None,
    *,
    allow_unknown: bool = False,
) -> TriageReport:
    """Classify a failure into the taxonomy and decide agent eligibility."""
    text = _collect_text(failures, logs)
    for category, signatures in _SIGNATURES:
        matched = tuple(signature for signature in signatures if signature in text)
        if matched:
            return TriageReport(
                category=category,
                eligible=category in _AGENT_ELIGIBLE,
                matched=matched,
                reason=f"matched {matched[0]!r} → {category.value}",
            )
    return TriageReport(
        category=FailureCategory.UNKNOWN,
        eligible=allow_unknown,
        matched=(),
        reason="no signature matched (defaults to escalation)",
    )
