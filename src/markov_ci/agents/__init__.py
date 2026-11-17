"""markov_ci.agents — the agent adapter seam and its implementations."""

from __future__ import annotations

from markov_ci.agents.base import AgentAdapter, PatchProposal, RepairContext
from markov_ci.agents.harness import (
    HarnessAgent,
    HarnessError,
    HarnessSpec,
    HarnessTimeout,
    Runner,
)
from markov_ci.agents.simulated import SimulatedAgent
from markov_ci.agents.templates import (
    TEMPLATES,
    HarnessTemplate,
    build_template_agent,
    template_spec,
)

__all__ = [
    "TEMPLATES",
    "AgentAdapter",
    "HarnessAgent",
    "HarnessError",
    "HarnessSpec",
    "HarnessTemplate",
    "HarnessTimeout",
    "PatchProposal",
    "RepairContext",
    "Runner",
    "SimulatedAgent",
    "build_template_agent",
    "template_spec",
]

