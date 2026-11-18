"""M13.27 (#111) — compile errors from the prior/curve resolution."""

from __future__ import annotations

import pytest

from markov_ci.config import ConfigCompileError, chain_from_config, success_curve
from markov_ci.data import load_default_config


def test_no_priors_at_all_is_an_error() -> None:
    config = load_default_config().model_copy(update={"priors": {}})
    with pytest.raises(ConfigCompileError, match="no priors"):
        chain_from_config(config, adapter="default", category="default")


def test_a_named_adapter_without_a_block_falls_back_to_default() -> None:
    assert success_curve(load_default_config(), "harness", "default")


def test_a_prior_shorter_than_max_attempts_is_an_error() -> None:
    config = load_default_config()
    short = config.priors["default"]["default"].model_copy(update={"success": [0.9]})
    config = config.model_copy(update={"priors": {"default": {"default": short}}})
    with pytest.raises(ConfigCompileError, match="max_attempts"):
        chain_from_config(config, category="default")


def test_an_unknown_category_is_an_error() -> None:
    with pytest.raises(ConfigCompileError, match="no prior for category"):
        chain_from_config(load_default_config(), category="nope")
