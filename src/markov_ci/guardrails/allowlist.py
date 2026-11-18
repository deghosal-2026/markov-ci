"""Write allowlist + always-denied set (docs/spec/0005-guardrails.md §1).

Enforced in the engine, never delegated to an agent or its harness. The
always-denied set is a hardcoded constant: configuration can add denials but can
never widen it.

Matching uses `pathspec`'s gitignore semantics (spec 0005 §1) and is
**case-insensitive**, so `.ENV` and `.env` are the same file to the guardrail.
"""

from __future__ import annotations

import posixpath
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pathspec

DEFAULT_ALLOW_WRITE: tuple[str, ...] = ("src/**", "tests/**")

# Never writable, regardless of configuration. Matched case-insensitively.
ALWAYS_DENIED: tuple[str, ...] = (
    # version control + CI systems
    ".git",
    ".git/**",
    ".github",
    ".github/**",
    ".gitlab-ci.yml",
    "**/.gitlab-ci.yml",
    ".travis.yml",
    "**/.travis.yml",
    "azure-pipelines.yml",
    "**/azure-pipelines.yml",
    "appveyor.yml",
    "**/appveyor.yml",
    "Jenkinsfile",
    "**/Jenkinsfile",
    ".circleci/**",
    "**/.circleci/**",
    ".buildkite/**",
    "**/.buildkite/**",
    "bitbucket-pipelines.yml",
    "**/bitbucket-pipelines.yml",
    ".drone.yml",
    "**/.drone.yml",
    ".woodpecker.yml",
    "**/.woodpecker.yml",
    # build config for common systems
    "Dockerfile",
    "**/Dockerfile",
    "docker-compose.yml",
    "**/docker-compose.yml",
    "docker-compose.yaml",
    "**/docker-compose.yaml",
    "compose.yml",
    "**/compose.yml",
    "compose.yaml",
    "**/compose.yaml",
    "Makefile",
    "**/Makefile",
    "pyproject.toml",
    "**/pyproject.toml",
    "setup.py",
    "**/setup.py",
    "setup.cfg",
    "**/setup.cfg",
    "tox.ini",
    "**/tox.ini",
    ".pre-commit-config.yaml",
    "**/.pre-commit-config.yaml",
    "go.mod",
    "**/go.mod",
    "Cargo.toml",
    "**/Cargo.toml",
    "pom.xml",
    "**/pom.xml",
    "build.gradle",
    "**/build.gradle",
    "build.gradle.kts",
    "**/build.gradle.kts",
    "package.json",
    "**/package.json",
    # environment files
    ".env",
    ".env*",
    "**/.env*",
    "*.env",
    "**/*.env",
    "**/secrets/**",
    "secrets/**",
    # ownership
    "CODEOWNERS",
    "**/CODEOWNERS",
    # credentials and keys
    "*.pem",
    "**/*.pem",
    "*.key",
    "**/*.key",
    "*.p12",
    "**/*.p12",
    "*.pfx",
    "**/*.pfx",
    "*.jks",
    "**/*.jks",
    "*.keystore",
    "**/*.keystore",
    "id_rsa",
    "**/id_rsa",
    "id_dsa",
    "**/id_dsa",
    "id_ecdsa",
    "**/id_ecdsa",
    "id_ed25519",
    "**/id_ed25519",
    ".netrc",
    "**/.netrc",
    ".npmrc",
    "**/.npmrc",
    ".pypirc",
    "**/.pypirc",
    "credentials",
    "**/credentials",
    "*service-account*.json",
    "**/*service-account*.json",
    "**/.aws/**",
    "**/.ssh/**",
    # license + lockfiles
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


def _compile(patterns: Sequence[str]) -> pathspec.PathSpec[Any]:
    """Compile gitignore-style patterns, lower-cased for case-insensitive matching."""
    return pathspec.PathSpec.from_lines("gitignore", [p.lower() for p in patterns])


_ALWAYS_DENIED_SPEC = _compile(ALWAYS_DENIED)


def _matches(path: str, spec: pathspec.PathSpec[Any]) -> str | None:
    """Return the pattern that matches ``path`` (case-insensitively), or ``None``."""
    lowered = path.lower()
    for pattern in spec.patterns:
        if pattern.include and pattern.match_file(lowered):
            return str(pattern.pattern)
    return None


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
    allow_spec = _compile(allow_write)
    deny_spec = _compile(deny_write)

    offending: list[str] = []
    for raw_path in files:
        path, unsafe = _normalize(raw_path)
        if unsafe:
            offending.append(f"{raw_path}: absolute or traversing path")
            continue
        denied_by = _matches(path, _ALWAYS_DENIED_SPEC)
        if denied_by is not None:
            offending.append(f"{path}: always-denied ({denied_by})")
            continue
        custom = _matches(path, deny_spec)
        if custom is not None:
            offending.append(f"{path}: denied by config ({custom})")
            continue
        if _matches(path, allow_spec) is None:
            offending.append(f"{path}: not in the allowlist")

    if offending:
        return GuardrailDecision(
            allowed=False,
            reason=f"{len(offending)} path(s) denied",
            offending=tuple(offending),
        )
    return GuardrailDecision(allowed=True, reason="all paths permitted", offending=())
