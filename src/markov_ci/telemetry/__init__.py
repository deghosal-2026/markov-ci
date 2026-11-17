"""markov_ci.telemetry — the versioned event contract and run evidence."""

from __future__ import annotations

from markov_ci.telemetry.events import (
    SCHEMA_VERSION,
    JsonlSink,
    RunResult,
    TransitionEvent,
    utc_now,
)

__all__ = [
    "SCHEMA_VERSION",
    "JsonlSink",
    "RunResult",
    "TransitionEvent",
    "utc_now",
]

