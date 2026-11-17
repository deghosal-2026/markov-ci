"""Telemetry events and run results (docs/spec/0007-telemetry-events.md, spec 0011 §4).

Events are append-and-flush JSONL: a killed run leaves a valid partial stream, and
the absence of a terminal event is itself auditable. The JSON Schema in
``schemas/transition-event.schema.json`` is the single source of truth.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = 1


def utc_now() -> str:
    """Return the current time as an ISO-8601 UTC timestamp ending in ``Z``."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    """One structured state-transition record."""

    event: str
    run_id: str
    commit_sha: str
    pr_number: int | None
    from_state: str
    to_state: str
    duration_ms: int
    tokens_used: int
    failure_category: str
    attempt: int
    adapter: str
    ts: str
    schema_version: int = SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event": self.event,
            "run_id": self.run_id,
            "commit_sha": self.commit_sha,
            "pr_number": self.pr_number,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "failure_category": self.failure_category,
            "attempt": self.attempt,
            "adapter": self.adapter,
            "ts": self.ts,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True)


class JsonlSink:
    """Append-and-flush JSONL sink — crash-safe by construction."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle: TextIO = self._path.open("a", encoding="utf-8")

    def emit(self, event: TransitionEvent) -> None:
        self._handle.write(event.to_json() + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> JsonlSink:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class RunResult:
    """The complete evidence trail for one governed run."""

    absorbing_state: str | None
    visits: Mapping[str, int]
    tokens_used: int
    wall_clock_ms: int
    guardrail_report: tuple[str, ...]
    events_path: str | None
    patch_branch: str | None
    mandatory_review: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "absorbing_state": self.absorbing_state,
            "visits": dict(self.visits),
            "tokens_used": self.tokens_used,
            "wall_clock_ms": self.wall_clock_ms,
            "guardrail_report": list(self.guardrail_report),
            "events_path": self.events_path,
            "patch_branch": self.patch_branch,
            "mandatory_review": self.mandatory_review,
        }
