"""Log minimization (docs/spec/0010-triage.md §3).

Passing a 50k-line log into an agent degrades reasoning accuracy, inflates latency,
and burns tokens. This extracts the failing block, the relevant log/stack-trace
lines, and the diff — hard-capped at 200 lines — and scrubs secret-shaped strings.

The failing block is placed first so it survives head-truncation.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from markov_ci.triage.junit import TestFailure

MAX_LINES = 200

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|passwd|token|secret|api[_-]?key)\b\s*[:=]\s*\S+"),
)

_REDACTED = "[REDACTED]"


@dataclass(frozen=True, slots=True)
class MinimizedContext:
    """The minimized context passed to an agent."""

    text: str
    line_count: int
    truncated: bool
    redactions: int


def _scrub(line: str) -> tuple[str, int]:
    count = 0
    for pattern in _SECRET_PATTERNS:
        line, replacements = pattern.subn(_REDACTED, line)
        count += replacements
    return line, count


def minimize(
    failures: Sequence[TestFailure],
    logs: str | None = None,
    diff: str | None = None,
    max_lines: int = MAX_LINES,
) -> MinimizedContext:
    """Build a minimized context, capped at ``max_lines`` and free of secrets."""
    if max_lines < 1:
        raise ValueError(f"max_lines must be >= 1, got {max_lines}")

    lines: list[str] = []
    if failures:
        lines.append("## failing tests")
        lines.extend(
            f"[{failure.kind}] {failure.name}: {failure.message}"
            for failure in failures
        )
    if logs:
        lines.append("## log")
        lines.extend(logs.splitlines())
    if diff:
        lines.append("## diff")
        lines.extend(diff.splitlines())

    scrubbed: list[str] = []
    redactions = 0
    for line in lines:
        clean, count = _scrub(line)
        scrubbed.append(clean)
        redactions += count

    truncated = len(scrubbed) > max_lines
    kept = scrubbed[:max_lines]
    return MinimizedContext(
        text="\n".join(kept),
        line_count=len(kept),
        truncated=truncated,
        redactions=redactions,
    )
