"""M6.1 (#29) — telemetry events + RunResult (docs/spec/0007, spec/0011 §3–4)."""

from __future__ import annotations

import json
from pathlib import Path

from markov_ci.telemetry import (
    SCHEMA_VERSION,
    JsonlSink,
    RunResult,
    TransitionEvent,
    utc_now,
)


def _event(**overrides: object) -> TransitionEvent:
    values: dict[str, object] = {
        "event": "transition",
        "run_id": "run_8f14e45f",
        "commit_sha": "9f104b6",
        "pr_number": 42,
        "from_state": "s2_agent_reasoning#1",
        "to_state": "s3_sandbox_validation#1",
        "duration_ms": 1234,
        "tokens_used": 180,
        "failure_category": "unit_assertion",
        "attempt": 1,
        "adapter": "simulated",
        "ts": "2026-11-16T09:41:07Z",
    }
    values.update(overrides)
    return TransitionEvent(**values)  # type: ignore[arg-type]


def test_event_carries_the_documented_fields() -> None:
    payload = _event().as_dict()
    expected = {
        "schema_version", "event", "run_id", "commit_sha", "pr_number",
        "from_state", "to_state", "duration_ms", "tokens_used",
        "failure_category", "attempt", "adapter", "ts",
        "synthetic", "gate_rejected", "config_hash", "model_version",
    }
    assert set(payload) == expected
    assert payload["schema_version"] == SCHEMA_VERSION


def test_event_serialises_to_json() -> None:
    payload = json.loads(_event().to_json())
    assert payload["adapter"] == "simulated"
    assert payload["attempt"] == 1


def test_pr_number_may_be_null() -> None:
    assert _event(pr_number=None).as_dict()["pr_number"] is None


def test_utc_now_is_iso8601_utc() -> None:
    stamp = utc_now()
    assert stamp.endswith("Z")
    assert "T" in stamp


def test_jsonl_sink_writes_one_event_per_line(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    with JsonlSink(path) as sink:
        sink.emit(_event())
        sink.emit(_event(from_state="s3_sandbox_validation#1", to_state="s4_regression_check"))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["from_state"] == "s2_agent_reasoning#1"


def test_jsonl_sink_flushes_so_a_partial_stream_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlSink(path)
    sink.emit(_event())
    sink.emit(_event())  # simulate a crash right after the second event
    # do not close: the bytes must already be on disk and parseable
    raw = path.read_text(encoding="utf-8").splitlines()
    assert len(raw) == 2
    assert all(json.loads(line) for line in raw)
    sink.close()


def test_jsonl_sink_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "events.jsonl"
    with JsonlSink(path) as sink:
        sink.emit(_event())
    assert path.is_file()


def test_run_result_exposes_evidence() -> None:
    result = RunResult(
        absorbing_state="a1_ready_for_human_review",
        visits={"s0_deterministic_verify": 1, "s2_agent_reasoning#1": 1},
        tokens_used=180,
        wall_clock_ms=5000,
        guardrail_report=(),
        events_path=".markov-ci/events.jsonl",
        patch_branch="ai-fix/pr-42",
    )
    payload = result.as_dict()
    assert payload["absorbing_state"] == "a1_ready_for_human_review"
    assert payload["patch_branch"] == "ai-fix/pr-42"
    assert payload["visits"]["s2_agent_reasoning#1"] == 1


def test_run_result_without_a_patch() -> None:
    result = RunResult(
        absorbing_state="a2_escalate_to_author",
        visits={},
        tokens_used=0,
        wall_clock_ms=10,
        guardrail_report=("assertion deleted",),
        events_path=None,
        patch_branch=None,
    )
    assert result.as_dict()["patch_branch"] is None
    assert result.as_dict()["guardrail_report"] == ["assertion deleted"]
