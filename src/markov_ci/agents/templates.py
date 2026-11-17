"""Verified harness templates (docs/spec/0006-agent-adapters.md §3, PRD 07).

Each template is a **T2** invocation pattern (a named, tested headless command for
a known harness). The generic BYO-command adapter (**T3**) is `HarnessAgent` driven
by a user-supplied template.

`tested_versions` records the harness CLI versions a template was authored/verified
against. It is `"unverified"` until a maintainer runs the template against a live
CLI — live verification is **not** performed in this repo's CI, which is
deliberately offline (spec 0006 §3). Contribution of measured versions is welcome.
"""

from __future__ import annotations

from dataclasses import dataclass

from markov_ci.agents.harness import HarnessAgent, HarnessSpec, Runner


@dataclass(frozen=True, slots=True)
class HarnessTemplate:
    """A named, offline-tested invocation pattern for a harness CLI."""

    name: str
    id: str
    command_template: str
    timeout_seconds: int = 300
    tested_versions: str = "unverified"


TEMPLATES: dict[str, HarnessTemplate] = {
    "claude-code": HarnessTemplate(
        name="claude-code",
        id="claude-code",
        command_template='claude -p --output-format json "%PROMPT%"',
    ),
    "opencode": HarnessTemplate(
        name="opencode",
        id="opencode",
        command_template='opencode run "%PROMPT%"',
    ),
    "aider": HarnessTemplate(
        name="aider",
        id="aider",
        command_template='aider --yes-always --message "%PROMPT%"',
    ),
}


def template_spec(name: str) -> HarnessSpec:
    """Return the `HarnessSpec` for a named template."""
    template = TEMPLATES[name]
    return HarnessSpec(
        command_template=template.command_template,
        timeout_seconds=template.timeout_seconds,
        id=template.id,
    )


def build_template_agent(name: str, *, runner: Runner | None = None) -> HarnessAgent:
    """Build a `HarnessAgent` for a named template."""
    return HarnessAgent(template_spec(name), runner=runner)
