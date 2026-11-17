"""M2.4 (#18) — validate + analyze CLI (docs/spec/0008-cli-contract.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from markov_ci.cli import app

RUNNER = CliRunner()


def _write(tmp_path: Path, text: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_validate_default_config_exits_zero() -> None:
    result = RUNNER.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "ok" in result.stdout.lower() or "valid" in result.stdout.lower()


def test_validate_reports_counts() -> None:
    result = RUNNER.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "transient" in result.stdout


def test_validate_invalid_config_exits_four(tmp_path: Path) -> None:
    path = _write(tmp_path, "version: 2\nstates: {}\ntransitions: []\n")
    result = RUNNER.invoke(app, ["validate", path])
    assert result.exit_code == 4


def test_validate_missing_file_exits_four(tmp_path: Path) -> None:
    result = RUNNER.invoke(app, ["validate", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 4


def test_analyze_default_runs_and_reports_golden_numbers() -> None:
    result = RUNNER.invoke(app, ["analyze"])
    assert result.exit_code == 0
    assert "0.9" in result.stdout  # P(a1|s0) ≈ 0.92


def test_analyze_json_is_machine_readable() -> None:
    result = RUNNER.invoke(app, ["analyze", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["category"] == "default"
    assert "absorption_probabilities" in payload
    assert "a1_ready_for_human_review" in payload["absorption_probabilities"]
    assert payload["absorption_probabilities"]["a1_ready_for_human_review"] == pytest.approx(
        0.92, abs=0.01
    )


def test_analyze_with_category() -> None:
    result = RUNNER.invoke(app, ["analyze", "--category", "unit_assertion"])
    assert result.exit_code == 0


def test_analyze_invalid_config_exits_four(tmp_path: Path) -> None:
    path = _write(tmp_path, "version: 2\nstates: {}\ntransitions: []\n")
    result = RUNNER.invoke(app, ["analyze", path])
    assert result.exit_code == 4


def test_analyze_unknown_category_exits_four() -> None:
    result = RUNNER.invoke(app, ["analyze", "--category", "not_a_category"])
    assert result.exit_code == 4
