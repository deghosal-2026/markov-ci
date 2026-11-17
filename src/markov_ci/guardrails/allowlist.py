"""Write allowlist + always-denied set (docs/spec/0005-guardrails.md §1).

Enforced in the engine, never delegated to an agent or its harness. The
always-denied set is a hardcoded constant: configuration can add denials but can
never widen it.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_ALLOW_WRITE: tuple[str, ...] = ("src/**", "tests/**")

# Never writable, regardless of configuration.
ALWAYS_DENIED: tuple[str, ...] = (
    ".github/**",
    ".github",
    ".git/**",
    ".git",
    ".gitlab-ci.yml",
    "**/.gitlab-ci.yml",
    "Jenkinsfile",
    "**/Jenkinsfile",
    ".circleci/**",
    "*.env",
    "**/*.env",
    ".env",
    "**/secrets/**",
    "secrets/**",
    "LICENSE",
    "**/LICENSE",
    "*.lock",
    "**/*.lock",
    "package-lock.json",
    "**/package-lock.json",
)


@dataclass(frozen=True, slots=True)
class GuardrailDecision:
    """The outcome of checking a set of paths."""

    allowed: bool
    reason: str
    offending: tuple[str, ...]


def _translate(pattern: str) -> re.Pattern[str]:
    """Compile a gitignore-style glob (``**`` crosses directories, ``*`` does not)."""
    out = ["(?s:"]
    index, length = 0, len(pattern)
    while index < length:
        char = pattern[index]
        if char == "*":
            if index + 1 < length and pattern[index + 1] == "*":
                if index + 2 < length and pattern[index + 2] == "/":
                    out.append("(?:.*/)?")
                    index += 3
                else:
                    out.append(".*")
                    index += 2
            else:
                out.append("[^/]*")
                index += 1
        elif char == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    out.append(r")\Z")
    return re.compile("".join(out))


_TRANSLATED: dict[str, re.Pattern[str]] = {}


def _matches(path: str, pattern: str) -> bool:
    compiled = _TRANSLATED.get(pattern)
    if compiled is None:
        compiled = _translate(pattern)
        _TRANSLATED[pattern] = compiled
    return compiled.match(path) is not None


def _normalize(path: str) -> tuple[str, bool]:
    """Return ``(normalized, unsafe)`` — ``unsafe`` for absolute/escaping paths."""
    normalized = path.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("~"):
        return normalized, True
    collapsed = posixpath.normpath(normalized)
    if collapsed.startswith("..") or collapsed.startswith("/"):
        return collapsed, True
    return collapsed, False


def check_paths(
    files: Sequence[str],
    *,
    allow_write: Sequence[str] = DEFAULT_ALLOW_WRITE,
    deny_write: Sequence[str] = (),
) -> GuardrailDecision:
    """Return whether every path may be written, with reasons for any denial."""
    offending: list[str] = []
    for raw_path in files:
        path, unsafe = _normalize(raw_path)
        if unsafe:
            offending.append(f"{raw_path}: absolute or traversing path")
            continue
        denied_by = next(
            (pattern for pattern in ALWAYS_DENIED if _matches(path, pattern)),
            None,
        )
        if denied_by is not None:
            offending.append(f"{path}: always-denied ({denied_by})")
            continue
        custom = next((pattern for pattern in deny_write if _matches(path, pattern)), None)
        if custom is not None:
            offending.append(f"{path}: denied by config ({custom})")
            continue
        if not any(_matches(path, pattern) for pattern in allow_write):
            offending.append(f"{path}: not in the allowlist")

    if offending:
        return GuardrailDecision(
            allowed=False,
            reason=f"{len(offending)} path(s) denied",
            offending=tuple(offending),
        )
    return GuardrailDecision(allowed=True, reason="all paths permitted", offending=())
