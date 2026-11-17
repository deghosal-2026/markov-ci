"""Pydantic models for the config schema (docs/spec/0003-config-format.md).

Unknown keys are **forbidden** — a silently ignored typo means the user believes
they configured one thing while the engine does another, which is the worst
possible failure mode for a governance tool.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from markov_ci.policy import Policy


class StateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["transient", "absorbing"]
    loop_capable: bool = False


class TransitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source: str = Field(alias="from")
    target: str = Field(alias="to")
    probability: float
    per_attempt: bool = False


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_confidence: float = 0.40
    max_attempts: int = 3
    max_tokens: int = 200_000
    wall_clock_seconds: int = 900

    def to_policy(self) -> Policy:
        return Policy(
            min_confidence=self.min_confidence,
            max_attempts=self.max_attempts,
            max_tokens=self.max_tokens,
            wall_clock_seconds=self.wall_clock_seconds,
        )


class PriorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: list[float]
    cost_weight: float = 1.0
    source: Literal["prior", "empirical"] = "prior"


class HarnessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_template: str
    timeout_seconds: int = 300


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter: Literal["simulated", "harness", "command"] = "simulated"
    allow_write: list[str] = Field(default_factory=lambda: ["src/**", "tests/**"])
    deny_write: list[str] = Field(default_factory=list)
    harness: HarnessConfig | None = None


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sink: Literal["file", "none"] = "file"
    path: str = ".markov-ci/events.jsonl"


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    states: dict[str, StateConfig]
    transitions: list[TransitionConfig]
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    priors: dict[str, dict[str, PriorConfig]] = Field(default_factory=dict)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    @property
    def absorbing_ids(self) -> frozenset[str]:
        return frozenset(
            state_id
            for state_id, state in self.states.items()
            if state.type == "absorbing"
        )
