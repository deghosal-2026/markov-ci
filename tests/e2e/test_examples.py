"""M9.1 (#41) — the example proof-suite enforcer (docs/WBS.md M9 convention).

Every ``examples/<NN>-<name>/`` directory ships a ``README.md`` carrying the run
command, the expected output/event stream, the expected exit code, and the two
proof sections — **"What this proves"** and **"Forecast vs. actual"**.

Examples come in two shapes:

* **CLI demos** — the README's ``markov-ci <subcommand>`` command is executed here
  verbatim (docs-are-tests): its exit code is checked against the declaration, and
  its deterministic result is asserted stable across two identical seeded runs.
* **Workflow demos** (e.g. 05-github-actions-e2e) — a *live* GitHub Actions example;
  it ships a workflow that uses the Action and is exercised on a real PR, not offline.

The demo trees are made real git repositories once per session by
``tests/conftest.py`` (the sandbox applies patches in git worktrees).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import Result
from typer.testing import CliRunner

from markov_ci.cli import app

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
RUNNER = CliRunner()

_EXIT_LINE = re.compile(r"exit code to expect:\*\*\s*`(\d+)`", re.IGNORECASE)
_CMD_LINE = re.compile(r"^markov-ci [a-z][a-z-]*\b.*", re.MULTILINE)
_EXPECTED_SECTION = re.compile(r"^## Expected (event stream|output)\b", re.MULTILINE)
_ACTION_USE = re.compile(r"uses:\s*(\./|deghosal-2026/markov-ci)")


def _example_dirs() -> list[Path]:
    return sorted(p for p in EXAMPLES.glob("[0-9][0-9]-*") if p.is_dir())


def _readme_text(example: Path) -> str:
    readme = example / "README.md"
    return readme.read_text(encoding="utf-8") if readme.is_file() else ""


def _readme(example: Path) -> str:
    text = _readme_text(example)
    assert text, f"{example.name} is missing README.md"
    return text


def _workflow_files(example: Path) -> list[Path]:
    return sorted(p for p in example.glob("*.y*ml"))


def _cli_examples() -> list[Path]:
    return [p for p in _example_dirs() if _CMD_LINE.search(_readme_text(p))]


def _workflow_examples() -> list[Path]:
    return [p for p in _example_dirs() if not _CMD_LINE.search(_readme_text(p))]


def _run_tokens(readme: str) -> list[str]:
    """The first ``markov-ci <subcommand> ...`` command in the README's bash blocks."""
    lines = readme.splitlines()
    for index, line in enumerate(lines):
        if _CMD_LINE.match(line.strip()):
            command = line.strip()
            while command.endswith("\\") and index + 1 < len(lines):
                index += 1
                command = command[:-1].rstrip() + " " + lines[index].strip()
            return shlex.split(command)[1:]  # drop the `markov-ci` prefix
    pytest.fail("README has no `markov-ci` command to execute")


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
    assert _EXPECTED_SECTION.search(text), (
        "README needs an '## Expected output' or '## Expected event stream' section"
    )
    assert _declared_exit_code(text) in {0, 2, 3}


def test_every_example_is_a_cli_demo_or_a_workflow_demo() -> None:
    for example in _example_dirs():
        has_command = bool(_CMD_LINE.search(_readme_text(example)))
        has_workflow = bool(_workflow_files(example))
        assert has_command or has_workflow, (
            f"{example.name} ships neither a `markov-ci` command nor a workflow"
        )


@pytest.mark.parametrize("example", _cli_examples(), ids=lambda p: p.name)
def test_cli_example_run_reproduces_its_declared_exit_code(example: Path) -> None:
    readme = _readme(example)
    result = RUNNER.invoke(app, _run_tokens(readme))
    assert result.exit_code == _declared_exit_code(readme), result.stdout


@pytest.mark.parametrize("example", _cli_examples(), ids=lambda p: p.name)
def test_cli_example_run_is_deterministic_under_seed(example: Path) -> None:
    readme = _readme(example)
    tokens = [*_run_tokens(readme), "--json"]

    def _invoke() -> Result:
        return RUNNER.invoke(app, tokens)

    first = _invoke()
    second = _invoke()
    assert first.exit_code == second.exit_code == _declared_exit_code(readme)

    def _stable(payload: str) -> object:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return payload  # a triage short-circuit prints a constant line
        if "absorbing_state" not in data:
            return data  # `queue` output is fully deterministic
        return {key: data[key] for key in ("absorbing_state", "visits", "tokens_used")}

    assert _stable(first.stdout) == _stable(second.stdout)


@pytest.mark.parametrize("example", _workflow_examples(), ids=lambda p: p.name)
def test_workflow_example_ships_a_workflow_using_the_action(example: Path) -> None:
    files = _workflow_files(example)
    assert files, f"{example.name} is a workflow demo but ships no workflow file"
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert _ACTION_USE.search(text), (
        f"{example.name}'s workflow must use the Action (`uses: ./` or the published ref)"
    )


def _example_scripts() -> list[Path]:
    return sorted(EXAMPLES.glob("[0-9][0-9]-*/*.py"))


@pytest.mark.parametrize("script", _example_scripts(), ids=lambda p: p.parent.name)
def test_example_report_scripts_run(script: Path) -> None:
    """A shipped example report script (e.g. the burst report) must run clean."""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "report script printed nothing"
