"""Headless harness adapter (docs/spec/0006-agent-adapters.md §3, ADR-0016).

Drives a real coding-agent harness in headless mode (``claude -p``,
``opencode run``, ``aider --yes-always``, …) and turns its output into a
`PatchProposal`. The subprocess runner and timeout are injected so tests stay
offline and deterministic.

The template is split with `shlex.split` *before* ``%PROMPT%`` is substituted and
the process runs with ``shell=False`` (ADR-0016), so the prompt is a single argv
element and can never be re-interpreted as shell syntax. Governance
(allow-list, budgets, worktree validation) is enforced by the engine, **not** delegated to the
harness.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from markov_ci.agents.base import PatchProposal, RepairContext
from markov_ci.scrub import scrubbed_env

PROMPT_PLACEHOLDER = "%PROMPT%"
PROMPT_FILE_PLACEHOLDER = "%PROMPT_FILE%"
PROMPT_PLACEHOLDERS = (PROMPT_PLACEHOLDER, PROMPT_FILE_PLACEHOLDER)

# Shells whose `-c` / `/c` flag would re-parse the prompt (ADR-0016 §5).
_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "pwsh", "powershell", "cmd"})
_C_FLAGS = frozenset({"-c", "/c"})

_FENCE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)
_TOKENS = re.compile(r"""tokens?[_ ]?used"?\s*[:=]\s*(\d+)""", re.IGNORECASE)
_NEW_FILE = re.compile(r"^\+\+\+\s+b/(.+)$", re.MULTILINE)


class HarnessError(RuntimeError):
    """Raised when a harness cannot be invoked."""


class HarnessTimeout(HarnessError):
    """Raised when a harness exceeds its wall-clock bound."""


def _usage_tokens(text: str) -> int | None:
    """Parse real usage from a harness's JSON output (e.g. claude's ``usage``)."""
    for candidate in [text, *text.splitlines()]:
        candidate = candidate.strip()
        if not candidate.startswith("{"):
            continue
        try:
            payload = json.loads(candidate)
        except ValueError:
            continue
        usage = payload.get("usage") if isinstance(payload, dict) else None
        if isinstance(usage, dict):
            total = sum(
                value for key, value in usage.items()
                if key.endswith("_tokens") and isinstance(value, int)
            )
            if total:
                return total
    return None


def parse_harness_output(text: str) -> tuple[str, int | None]:
    """Return ``(diff, tokens_used)`` parsed from harness stdout.

    ``tokens_used`` is ``None`` when the harness reports no usage — the caller must
    not pretend it is zero (the token cap then does not bind; spec 0007).
    """
    tokens = _usage_tokens(text)
    if tokens is None:
        match = _TOKENS.search(text)
        tokens = int(match.group(1)) if match else None
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
    return prompt


def build_argv(
    command_template: str, prompt: str, *, prompt_file: str | None = None,
) -> list[str]:
    """Split the template, then substitute the prompt placeholders (ADR-0016).

    The split happens **before** substitution, so the prompt lands in exactly one
    argv element and can never be re-parsed as shell syntax. ``%PROMPT_FILE%`` is
    replaced with ``prompt_file`` (a path) when the template uses it.
    """
    argv: list[str] = []
    for part in shlex.split(command_template):
        if prompt_file is not None:
            part = part.replace(PROMPT_FILE_PLACEHOLDER, prompt_file)
        argv.append(part.replace(PROMPT_PLACEHOLDER, prompt))
    return argv


def validate_template(command_template: str) -> None:
    """Raise `ValueError` when a harness command template is invalid (ADR-0016).

    Called at config load, so a broken template fails as invalid config (exit 4)
    rather than mid-run (exit 2). Checks: non-empty, parseable by `shlex`,
    contains ``%PROMPT%`` or ``%PROMPT_FILE%``, and does not use ``%PROMPT%`` as
    the program name.
    """
    if not command_template.strip():
        raise ValueError("harness command template must not be empty")
    try:
        argv = shlex.split(command_template)
    except ValueError as exc:
        raise ValueError(
            f"harness command template is not parseable: {exc}",
        ) from exc
    if not argv:
        raise ValueError("harness command template must not be empty")
    if not any(placeholder in command_template for placeholder in PROMPT_PLACEHOLDERS):
        raise ValueError(
            "harness command template must contain %PROMPT% or %PROMPT_FILE%",
        )
    if argv[0] == PROMPT_PLACEHOLDER:
        raise ValueError(
            f"{PROMPT_PLACEHOLDER} must not be the program name",
        )
    _reject_shell_reentry(argv)


def _reject_shell_reentry(argv: list[str]) -> None:
    """Reject a template that hands the prompt to a shell's ``-c`` script (ADR-0016 §5).

    The safe positional form — ``bash -c 'tool "$1"' _ %PROMPT%`` — stays allowed
    because the prompt is a positional argument, not part of the ``-c`` script.
    """
    program = argv[0].replace("\\", "/").rsplit("/", 1)[-1]
    if program.endswith(".exe"):
        program = program[:-4]
    if program not in _SHELLS:
        return
    for index, part in enumerate(argv):
        if part in _C_FLAGS:
            script = argv[index + 1] if index + 1 < len(argv) else ""
            if PROMPT_PLACEHOLDER in script:
                raise ValueError(
                    "harness command template must not pass %PROMPT% to a shell "
                    f"via {part!r}; keep the prompt positional, e.g. "
                    "bash -c 'tool \"$1\"' _ %PROMPT%",
                )
            return


def git_diff_in(cwd: str | Path) -> str:
    """Return the working-tree diff of ``cwd`` (tracked changes + untracked files).

    Used to derive a proposal from the *tree* the harness edited (ADR-0012 §2),
    rather than trusting whatever the harness printed. Read-only: it never stages.
    """
    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, check=False,
        ).stdout

    parts = [_git("diff", "-M", "HEAD")]
    untracked = _git("ls-files", "--others", "--exclude-standard").splitlines()
    for name in untracked:
        parts.append(_git("diff", "--no-index", "--", "/dev/null", name))
    return "".join(parts)


def _default_runner(
    argv: Sequence[str],
    *,
    timeout: int,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # argv-only invocation (ADR-0016): no shell, so the prompt can never be
    # re-interpreted as shell syntax. Governance — allowlists, budgets, caps,
    # worktree validation — is enforced by the engine on the proposal, never
    # delegated to the harness.
    return subprocess.run(
        list(argv),
        shell=False,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


class Runner(Protocol):
    """A callable that runs an argv and returns its completed process."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True, slots=True)
class HarnessSpec:
    """How to invoke a harness."""

    command_template: str
    timeout_seconds: int = 300
    id: str = "harness"


class HarnessAgent:
    """An adapter that drives a harness CLI in headless mode."""

    def __init__(
        self,
        spec: HarnessSpec,
        *,
        runner: Runner | None = None,
        cwd: str | Path | None = None,
        env_allow: Sequence[str] = (),
        home: str | Path | None = None,
    ) -> None:
        self.spec = spec
        self.id = spec.id
        self._runner = runner or _default_runner
        self._cwd = cwd
        self._env_allow = tuple(env_allow)
        self._home = home

    def _env(self) -> dict[str, str]:
        home = self._home
        if home is None:
            home = tempfile.mkdtemp(prefix="markov-harness-home-")
            self._home = home
        return scrubbed_env(home=home, allow=self._env_allow)

    def repair(self, ctx: RepairContext) -> PatchProposal:
        prompt = _build_prompt(ctx)
        template = self.spec.command_template
        timeout = self.spec.timeout_seconds
        if ctx.timeout is not None:
            timeout = min(timeout, ctx.timeout)
        if PROMPT_FILE_PLACEHOLDER in template:
            completed = self._run_with_prompt_file(template, prompt, timeout=timeout)
        else:
            completed = self._run(build_argv(template, prompt), timeout=timeout)

        diff = self._proposal_diff(completed.stdout)
        _, tokens = parse_harness_output(completed.stdout)
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

    def _proposal_diff(self, stdout: str) -> str:
        """Prefer the tree's ``git diff``; fall back to parsing stdout (M13.19)."""
        if self._cwd is not None and (Path(self._cwd) / ".git").exists():
            tree_diff = git_diff_in(self._cwd)
            if tree_diff.strip():
                return tree_diff
        return parse_harness_output(stdout)[0]

    def _run(
        self, argv: list[str], *, timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(
                argv, timeout=timeout, cwd=self._cwd, env=self._env(),
            )
        except subprocess.TimeoutExpired as exc:
            raise HarnessTimeout(f"harness exceeded {timeout}s") from exc
        except OSError as exc:
            raise HarnessError(f"could not invoke harness: {exc}") from exc

    def _run_with_prompt_file(
        self, template: str, prompt: str, *, timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """Write the prompt to a ``0600`` temp file, run, then always clean up."""
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed in finally
            mode="w", encoding="utf-8", prefix="markov-ci-prompt-", suffix=".txt",
            delete=False,
        )
        path = handle.name
        try:
            os.chmod(path, 0o600)
            handle.write(prompt)
            handle.close()
            return self._run(
                build_argv(template, prompt, prompt_file=path), timeout=timeout,
            )
        finally:
            if not handle.closed:
                handle.close()
            os.unlink(path)
