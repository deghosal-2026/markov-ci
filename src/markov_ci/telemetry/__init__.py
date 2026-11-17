"""markov_ci.telemetry — the versioned event contract and run evidence."""

from __future__ import annotations

from markov_ci.telemetry.events import (
    SCHEMA_VERSION,
    JsonlSink,
    RunResult,
    TransitionEvent,
    utc_now,
)
from markov_ci.telemetry.recompute import recompute

__all__ = [
    "SCHEMA_VERSION",
    "JsonlSink",
    "RunResult",
    "TransitionEvent",
    "recompute",
    "utc_now",
]

