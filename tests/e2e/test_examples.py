"""M9.1 (#41) — the example proof-suite enforcer (docs/WBS.md M9 convention).

Every ``examples/<NN>-<name>/`` directory ships a ``README.md`` carrying the run
command, the expected exit code, the expected event stream, and the two proof
sections — **"What this proves"** and **"Forecast vs. actual"**. The documented
run command is executed here verbatim (docs-are-tests): its exit code is checked
against the README's declaration, and its deterministic result is asserted stable
across two identical seeded runs (same seed → same outcome).

The demo trees are made real git repositories once per session by
``tests/conftest.py`` (the sandbox applies patches in git worktrees).
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest
from click.testing import Result
from typer.testing import CliRunner

from markov_ci.cli import app

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
RUNNER = CliRunner()

_EXIT_LINE = re.compile(r"exit code to expect:\*\*\s*`(\d+)`", re.IGNORECASE)
_RUN_LINE = re.compile(r"^markov-ci run\b.*")


def _example_dirs() -> list[Path]:
    return sorted(p for p in EXAMPLES.glob("[0-9][0-9]-*") if p.is_dir())


def _readme(example: Path) -> str:
    readme = example / "README.md"
    assert readme.is_file(), f"{example.name} is missing README.md"
    return readme.read_text(encoding="utf-8")


def _run_tokens(readme: str) -> list[str]:
    """The first ``markov-ci run ...`` command in the README's bash blocks."""
    lines = readme.splitlines()
    for index, line in enumerate(lines):
        if _RUN_LINE.match(line.strip()):
            command = line.strip()
            while command.endswith("\\") and index + 1 < len(lines):
                index += 1
                command = command[:-1].rstrip() + " " + lines[index].strip()
            return shlex.split(command)[1:]  # drop the `markov-ci` prefix
    pytest.fail("README has no `markov-ci run` command to execute")


def _declared_exit_code(readme: str) -> int:
    match = _EXIT_LINE.search(readme)
    assert match, "README does not declare `**Exit code to expect:** `N``"
    return int(match.group(1))


def test_the_proof_suite_ships_at_least_one_example() -> None:
    assert _example_dirs(), "no examples/ directories found"


@pytest.mark.parametrize("example", _example_dirs(), ids=lambda p: p.name)
def test_every_example_readme_carries_both_proof_sections(example: Path) -> None:
    text = _readme(example)
    assert "## What this proves" in text
    assert "## Forecast vs. actual" in text
    assert _declared_exit_code(text) in {0, 2, 3}


@pytest.mark.parametrize("example", _example_dirs(), ids=lambda p: p.name)
def test_example_run_reproduces_its_declared_exit_code(example: Path) -> None:
    readme = _readme(example)
    result = RUNNER.invoke(app, _run_tokens(readme))
    assert result.exit_code == _declared_exit_code(readme), result.stdout


@pytest.mark.parametrize("example", _example_dirs(), ids=lambda p: p.name)
def test_example_run_is_deterministic_under_seed(example: Path) -> None:
    readme = _readme(example)
    tokens = [*_run_tokens(readme), "--json"]

    def _invoke() -> Result:
        return RUNNER.invoke(app, tokens)

    first = _invoke()
    second = _invoke()
    assert first.exit_code == second.exit_code == _declared_exit_code(readme)

    def _stable(payload: str) -> dict[str, object]:
        data = json.loads(payload)
        return {key: data[key] for key in ("absorbing_state", "visits", "tokens_used")}

    assert _stable(first.stdout) == _stable(second.stdout)
