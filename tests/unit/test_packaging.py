"""M0.2 — packaging + tool configuration (docs/WBS.md acceptance criteria)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import markov_ci

ROOT = Path(__file__).resolve().parents[2]

CORE_DEP_NAMES = {"numpy", "pydantic", "pyyaml", "typer", "rich", "jsonschema"}
BANNED_CORE = ("anthropic", "openai", "litellm", "langchain", "claude")


def _config() -> dict[str, Any]:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def _dep_name(spec: str) -> str:
    for sep in (">", "<", "=", "!", " ", ";"):
        spec = spec.split(sep)[0]
    return spec.strip().lower()


def test_pyproject_parses_and_is_named() -> None:
    assert _config()["project"]["name"] == "markov-ci"


def test_requires_python_is_311_or_newer() -> None:
    assert _config()["project"]["requires-python"] == ">=3.11"


def test_runtime_dependencies_are_exactly_the_core_set() -> None:
    deps = {_dep_name(d) for d in _config()["project"]["dependencies"]}
    assert deps == CORE_DEP_NAMES


def test_core_has_no_llm_or_harness_sdk() -> None:
    core = " ".join(_config()["project"]["dependencies"]).lower()
    assert not any(banned in core for banned in BANNED_CORE)


def test_dev_extra_has_the_toolchain() -> None:
    dev = " ".join(_config()["project"]["optional-dependencies"]["dev"]).lower()
    for tool in ("pytest", "hypothesis", "ruff", "mypy", "mkdocs"):
        assert tool in dev, f"{tool} missing from [dev]"


def test_console_script_entry_point() -> None:
    assert _config()["project"]["scripts"]["markov-ci"] == "markov_ci.cli:app"


def test_pytest_pythonpath_includes_src() -> None:
    opts = _config()["tool"]["pytest"]["ini_options"]
    assert "src" in opts["pythonpath"]
    assert "tests" in opts["testpaths"]


def test_mypy_is_strict() -> None:
    mypy = _config()["tool"]["mypy"]
    assert mypy["strict"] is True
    assert set(mypy["files"]) == {"src", "tests"}


def test_ruff_targets_py311() -> None:
    assert _config()["tool"]["ruff"]["target-version"] == "py311"


def test_version_matches_package() -> None:
    assert _config()["project"]["version"] == markov_ci.__version__


def test_coverage_gate_is_95_percent() -> None:
    report = _config()["tool"]["coverage"]["report"]
    assert report["fail_under"] == 95
    run = _config()["tool"]["coverage"]["run"]
    assert run["source"] == ["markov_ci"]
