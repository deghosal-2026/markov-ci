"""M6.5 (#33) — the telemetry JSON Schema artifact (docs/spec/0007-telemetry-events.md)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from markov_ci.telemetry import SCHEMA_VERSION, TransitionEvent

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "transition-event.schema.json"

REQUIRED = {
    "schema_version", "event", "run_id", "commit_sha", "pr_number",
    "from_state", "to_state", "duration_ms", "tokens_used",
    "failure_category", "attempt", "adapter", "ts",
}


def _schema() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return payload


def _event(**overrides: object) -> dict[str, Any]:
    base = TransitionEvent(
        event="transition",
        run_id="run_1",
        commit_sha="abc",
        pr_number=42,
        from_state="s2_agent_reasoning#1",
        to_state="s3_sandbox_validation#1",
        duration_ms=10,
        tokens_used=180,
        failure_category="unit_assertion",
        attempt=1,
        adapter="simulated",
        ts="2026-11-16T09:41:07Z",
    ).as_dict()
    base.update(overrides)
    return base


def test_schema_artifact_exists() -> None:
    assert SCHEMA_PATH.is_file()


def test_schema_is_valid_json_schema() -> None:
    Draft202012Validator.check_schema(_schema())


def test_schema_version_matches_the_emitter() -> None:
    assert _schema()["properties"]["schema_version"]["const"] == SCHEMA_VERSION


def test_required_fields_match_the_contract() -> None:
    assert set(_schema()["required"]) == REQUIRED


def test_an_emitted_event_validates() -> None:
    Draft202012Validator(_schema()).validate(_event())


def test_a_null_pr_number_validates() -> None:
    Draft202012Validator(_schema()).validate(_event(pr_number=None))


@pytest.mark.parametrize("missing", sorted(REQUIRED))
def test_missing_field_is_invalid(missing: str) -> None:
    event = _event()
    del event[missing]
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(event)


def test_extra_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(_event(token="secret"))


def test_negative_tokens_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(_event(tokens_used=-1))


def test_reference_page_lists_every_field() -> None:
    doc = (ROOT / "docs" / "reference" / "telemetry.md").read_text(encoding="utf-8")
    missing = [field for field in REQUIRED if f"`{field}`" not in doc]
    assert missing == [], f"reference/telemetry.md is missing: {missing}"
