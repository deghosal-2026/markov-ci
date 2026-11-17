"""Packaged default configuration (F11).

The default pipeline and its priors ship inside the wheel so that
``markov-ci analyze`` works with zero configuration.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from markov_ci.config import Config, load_config

__all__ = ["DEFAULT_CONFIG_NAME", "default_config_path", "load_default_config"]

DEFAULT_CONFIG_NAME = "default.yaml"


def default_config_path() -> Path:
    """Return the filesystem path of the packaged default config."""
    return Path(str(resources.files(__package__).joinpath(DEFAULT_CONFIG_NAME)))


def load_default_config() -> Config:
    """Load and validate the packaged default config."""
    return load_config(default_config_path())
