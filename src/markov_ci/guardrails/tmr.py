"""Test-modification-ratio checker (docs/spec/0005-guardrails.md §2).

An agent that "fixes" a failing test by weakening the assertion has destroyed the
suite's signal — the project's anti-pattern #1. This is a hard stop, not a warning.

``tmr = test_lines_changed / src_lines_changed``; a ratio above 1.0, any assertion
deletion, or a pure test change with no source change stops the run and flags the
patch for mandatory review.
"""

from __future__ import annotations

from dataclasses import dataclass

_RATIO_LIMIT = 1.0


@dataclass(frozen=True, slots=True)
class TMRResult:
    """The checker's verdict."""

    ratio: float
    test_lines_changed: int
    src_lines_changed: int
    assertion_deletions: int
    mandatory_review: bool
    stop: bool
    reason: str


def _is_test_path(path: str) -> bool:
    parts = path.split("/")
    if parts[0] in {"tests", "test"}:
        return True
    name = parts[-1]
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


def _changes(diff: str):  # type: ignore[no-untyped-def]
    """Yield ``(path, sign, text)`` for every added/removed content line."""
    current: str | None = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            current = path[2:] if path.startswith("b/") else path
            continue
        if line.startswith("--- "):
            continue
        if current is None or not line or line[0] not in {"+", "-"}:
            continue
        if line.startswith(("+++", "---")):
            continue
        yield current, line[0], line[1:]


def check_test_modification(diff: str) -> TMRResult:
    """Compute the test-modification ratio and the assertion-deletion check."""
    test_lines = 0
    src_lines = 0
    removed_asserts = 0
    added_asserts = 0

    for path, sign, text in _changes(diff):
        stripped = text.strip()
        if _is_test_path(path):
            test_lines += 1
        else:
            src_lines += 1
        if "assert" in stripped:
            if sign == "-":
                removed_asserts += 1
            else:
                added_asserts += 1

    # a *net* loss of assertions is a deletion; a rewrite (remove + add) is not
    deletions = max(0, removed_asserts - added_asserts)

    ratio = test_lines / src_lines if src_lines else (float("inf") if test_lines else 0.0)

    reasons: list[str] = []
    if deletions:
        reasons.append(f"{deletions} assertion(s) deleted")
    if src_lines == 0 and test_lines > 0:
        reasons.append("pure test change with no source change")
    elif ratio > _RATIO_LIMIT:
        reasons.append(
            f"test-modification ratio {ratio:.2f} exceeds {_RATIO_LIMIT:.1f}",
        )

    stop = bool(reasons)
    return TMRResult(
        ratio=ratio,
        test_lines_changed=test_lines,
        src_lines_changed=src_lines,
        assertion_deletions=deletions,
        mandatory_review=stop,
        stop=stop,
        reason="; ".join(reasons) if reasons else "no test-weakening detected",
    )
