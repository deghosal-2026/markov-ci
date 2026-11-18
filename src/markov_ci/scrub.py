"""Environment scrubbing for untrusted child processes (ADR-0012 §2, spec 0011 §2).

A validation child or a harness CLI runs with an **allowlisted** environment: only
`PATH`, `LANG` and a temp `HOME`, plus any variables the operator explicitly lists
in config. Credentials the CI runner injects — `GITHUB_TOKEN`, `ACTIONS_*`,
`*_TOKEN` / `*_KEY` / `*_SECRET` — never reach the child unless they are a
deliberate, config-listed opt-in; `GITHUB_TOKEN` and `ACTIONS_*` are hard-blocked
and can never be opted in.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path

# Always passed through (when present) so ordinary commands keep working.
BASE_ENV_VARS: tuple[str, ...] = ("PATH", "LANG")

_SECRET_SUFFIXES = ("_TOKEN", "_KEY", "_SECRET")
_HARD_BLOCKED = ("GITHUB_TOKEN",)
_HARD_BLOCKED_PREFIXES = ("ACTIONS_",)


def _hard_blocked(name: str) -> bool:
    upper = name.upper()
    return upper in _HARD_BLOCKED or upper.startswith(_HARD_BLOCKED_PREFIXES)


def is_secret(name: str) -> bool:
    """Return whether a variable name looks like a credential."""
    upper = name.upper()
    return _hard_blocked(name) or upper.endswith(_SECRET_SUFFIXES)


def scrubbed_env(
    *,
    home: str | Path,
    allow: Sequence[str] = (),
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return the allowlisted environment for an untrusted child process."""
    source: Mapping[str, str] = os.environ if base is None else base
    env: dict[str, str] = {
        name: source[name] for name in BASE_ENV_VARS if name in source
    }
    env["HOME"] = str(home)
    for name in allow:
        if name in source and not _hard_blocked(name):
            env[name] = source[name]
    return env


__all__ = ["BASE_ENV_VARS", "is_secret", "scrubbed_env"]
