"""Loading and validating config (docs/spec/0003-config-format.md).

Two layers of validation:

1. **schema** — pydantic models with ``extra="forbid"`` (unknown keys rejected);
2. **semantics** — deterministic checks pydantic can't express: version, dangling
   state references, edges leaving an absorbing state, and pre-augmented ids.

Structural validation (row sums) happens *after assembly* (spec 0002 §1.4), not here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from markov_ci.agents.harness import validate_template
from markov_ci.config.models import Config


class ConfigError(ValueError):
    """Raised when a config document is invalid."""


def _line_of(text: str, key: str) -> int | None:
    """Best-effort 1-based line number for a key in the raw YAML text."""
    token = f"{key}:"
    for number, line in enumerate(text.splitlines(), start=1):
        if token in line:
            return number
    return None


def _format_validation_error(error: ValidationError, text: str) -> str:
    lines: list[str] = []
    for problem in error.errors():
        location = ".".join(str(part) for part in problem["loc"])
        key = str(problem["loc"][-1]) if problem["loc"] else location
        line = _line_of(text, key)
        where = f"line {line}: " if line is not None else ""
        lines.append(f"{where}{location}: {problem['msg']}")
    return "; ".join(lines)


def _check_transitions(config: Config) -> None:
    known = set(config.states)
    absorbing = set(config.absorbing_ids)
    for transition in config.transitions:
        for endpoint in (transition.source, transition.target):
            if "#" in endpoint:
                raise ConfigError(
                    f"transition references pre-augmented state {endpoint!r}; "
                    "attempt-indexed states are generated, not declared",
                )
            if endpoint not in known:
                raise ConfigError(f"transition references unknown state {endpoint!r}")
        if transition.source in absorbing:
            raise ConfigError(
                f"edge leaves absorbing state {transition.source!r}; "
                "absorbing states cannot be left",
            )


def _check_harness(config: Config) -> None:
    """Validate the harness command template at load time (M13.2, ADR-0016)."""
    harness = config.agent.harness
    if harness is None:
        return
    try:
        validate_template(harness.command_template)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def parse_config(text: str) -> Config:
    """Parse and validate a config document from a YAML string."""
    try:
        raw: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("config document must be a mapping")

    # Check the version before the pydantic schema (M13.30): a v2 document should
    # fail with a version message, not a confusing schema error.
    raw_version = raw.get("version", 1)
    if raw_version != 1:
        raise ConfigError(f"unsupported config version {raw_version}; expected 1")

    try:
        config = Config.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc, text)) from exc

    _check_transitions(config)
    _check_harness(config)
    # re-validate the effective policy so bad thresholds fail at load time
    config.policy.to_policy()
    return config


def load_config(path: str | Path) -> Config:
    """Load and validate a config document from a file."""
    return parse_config(Path(path).read_text(encoding="utf-8"))
