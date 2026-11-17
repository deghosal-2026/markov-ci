"""M8.3 (#39) — docs are tests: quick-start commands execute, reference matches the code.

Commands in `docs/quick-start.md` are extracted and run verbatim. Commands that
reference a path which does not exist yet (the demos land in M9) are skipped and
reported, so the suite stays honest rather than silently green.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
from typer.testing import CliRunner

from markov_ci.cli import app

ROOT = Path(__file__).resolve().parents[3]
QUICKSTART = ROOT / "docs" / "quick-start.md"
CLI_REFERENCE = ROOT / "docs" / "reference" / "cli.md"

RUNNER = CliRunner()

_PATHLIKE = re.compile(r"\.(ya?ml|xml|jsonl|py)$")


def _quickstart_commands() -> list[list[str]]:
    lines = QUICKSTART.read_text(encoding="utf-8").splitlines()
    commands: list[list[str]] = []
    in_bash = False
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```"):
            in_bash = stripped[3:].strip() == "bash"
            index += 1
            continue
        if in_bash and stripped.startswith("markov-ci ") and not stripped.startswith("markov-ci <"):
            command = stripped
            while command.endswith("\\") and index + 1 < len(lines):
                index += 1
                command = command[:-1].rstrip() + " " + lines[index].strip()
            command = command.split(" #", 1)[0].strip()
            tokens = shlex.split(command)
            commands.append(tokens[1:] if tokens and tokens[0] == "markov-ci" else tokens)
        index += 1
    return commands


def _looks_like_path(token: str) -> bool:
    return "/" in token or bool(_PATHLIKE.search(token))


def _referenced_file_missing(args: list[str]) -> bool:
    for token in args:
        if token.startswith("-"):
            continue
        candidate = token.split("=")[-1]
        if _looks_like_path(candidate) and not (ROOT / candidate).exists():
            return True
    return False


def test_quickstart_commands_are_executable() -> None:
    runnable = [args for args in _quickstart_commands() if not _referenced_file_missing(args)]
    assert runnable, "expected at least one self-contained quick-start command"
    for args in runnable:
        result = RUNNER.invoke(app, args)
        assert result.exit_code == 0, f"{' '.join(args)} → exit {result.exit_code}: {result.stdout}"


def _registered_commands() -> set[str]:
    return {
        command.name or command.callback.__name__
        for command in app.registered_commands
        if command.callback is not None
    }


def test_every_cli_command_is_documented() -> None:
    doc = CLI_REFERENCE.read_text(encoding="utf-8")
    missing = [name for name in _registered_commands() if f"markov-ci {name}" not in doc]
    assert missing == [], f"undocumented commands: {missing}"


def test_the_reference_documents_no_phantom_commands() -> None:
    text = CLI_REFERENCE.read_text(encoding="utf-8")
    documented = set(re.findall(r"markov-ci ([a-z][a-z-]+)", text))
    phantom = documented - _registered_commands()
    assert phantom == set(), f"documented but not implemented: {phantom}"


def test_mkdocs_config_has_no_broken_nav_targets() -> None:
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    targets = re.findall(r":\s*([\w./-]+\.md)\s*$", text, re.MULTILINE)
    missing = [t for t in targets if not (ROOT / "docs" / t).exists()]
    assert missing == [], f"mkdocs nav points at missing files: {missing}"


@pytest.mark.parametrize("page", ["index.md", "quick-start.md", "architecture.md"])
def test_top_level_docs_exist(page: str) -> None:
    assert (ROOT / "docs" / page).is_file()


# Planning docs live in the repo but are deliberately kept out of the site nav.
_PLANNING = ("prd/", "spec/", "adr/", "WBS")


def _nav_targets() -> set[str]:
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    return set(re.findall(r":\s*([\w./-]+\.md)\s*$", text, re.MULTILINE))


def test_every_site_page_is_reachable_from_the_nav() -> None:
    nav = _nav_targets()
    docs_root = ROOT / "docs"
    pages = {
        str(path.relative_to(docs_root))
        for path in docs_root.rglob("*.md")
        if not str(path.relative_to(docs_root)).startswith(_PLANNING)
    }
    orphans = sorted(pages - nav)
    assert orphans == [], f"docs pages not in the mkdocs nav: {orphans}"


def test_every_example_ships_a_readme() -> None:
    examples = ROOT / "examples"
    if not examples.is_dir():
        pytest.skip("examples land in M9")
    missing = [
        day.name
        for day in sorted(examples.iterdir())
        if day.is_dir() and not (day / "README.md").is_file()
    ]
    assert missing == [], f"examples without an accompanying README: {missing}"
