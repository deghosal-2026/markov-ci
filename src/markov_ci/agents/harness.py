"""Headless harness adapter (docs/spec/0006-agent-adapters.md §3, ADR-0007).

Drives a real coding-agent harness in headless mode (``claude -p``,
``opencode run``, ``aider --yes-always``, …) and turns its output into a
`PatchProposal`. The subprocess runner and timeout are injected so tests stay
offline and deterministic.

Note: the command template is trusted configuration; governance
(allow-list, budgets, sandbox) is enforced by the engine, **not** delegated to the
harness.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Protocol

from markov_ci.agents.base import PatchProposal, RepairContext

_FENCE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)
_TOKENS = re.compile(r"""tokens?[_ ]?used"?\s*[:=]\s*(\d+)""", re.IGNORECASE)
_NEW_FILE = re.compile(r"^\+\+\+\s+b/(.+)$", re.MULTILINE)


class HarnessError(RuntimeError):
    """Raised when a harness cannot be invoked."""


class HarnessTimeout(HarnessError):
    """Raised when a harness exceeds its wall-clock bound."""


def parse_harness_output(text: str) -> tuple[str, int]:
    """Return ``(diff, tokens_used)`` parsed from harness stdout."""
    tokens_match = _TOKENS.search(text)
    tokens = int(tokens_match.group(1)) if tokens_match else 0
    fence = _FENCE.search(text)
    diff = fence.group(1).strip() if fence else ""
    return diff, tokens


def _files_changed(diff: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_NEW_FILE.findall(diff)))


def _build_prompt(ctx: RepairContext) -> str:
    prompt = (
        f"Fix this {ctx.category.value} failure (attempt {ctx.attempt}/"
        f"{ctx.max_attempts}).\n\n{ctx.context}"
    )
    if ctx.diff:
        prompt += f"\n\nDiff so far:\n{ctx.diff}"
    return prompt.replace('"', '\\"')


def _default_runner(command: str, *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S602 - trusted template, quoted prompt
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


class Runner(Protocol):
    """A callable that runs a command and returns its completed process."""

    def __call__(
        self, command: str, *, timeout: int,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True, slots=True)
class HarnessSpec:
    """How to invoke a harness."""

    command_template: str
    timeout_seconds: int = 300
    id: str = "harness"


class HarnessAgent:
    """An adapter that drives a harness CLI in headless mode."""

    def __init__(self, spec: HarnessSpec, *, runner: Runner | None = None) -> None:
        self.spec = spec
        self.id = spec.id
        self._runner = runner or _default_runner

    def repair(self, ctx: RepairContext) -> PatchProposal:
        prompt = _build_prompt(ctx)
        command = self.spec.command_template.replace("%PROMPT%", prompt)
        try:
            completed = self._runner(command, timeout=self.spec.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise HarnessTimeout(
                f"harness exceeded {self.spec.timeout_seconds}s",
            ) from exc
        except OSError as exc:
            raise HarnessError(f"could not invoke harness: {exc}") from exc

        diff, tokens = parse_harness_output(completed.stdout)
        if completed.returncode != 0 and not diff:
            return PatchProposal(
                diff="",
                rationale=f"harness exited {completed.returncode}",
                tokens_used=tokens,
            )
        return PatchProposal(
            diff=diff,
            rationale=f"harness patch ({self.id})",
            tokens_used=tokens,
            files_changed=_files_changed(diff),
        )
