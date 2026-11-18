"""M13.10 (#94) — property test: the diff-path parser vs real git (spec 0005 §1).

For any generated change set, every path git reports as touched must be caught by
the engine's parser — otherwise a patch could smuggle a path past the allowlist.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from markov_ci.guardrails.diffpaths import parse_diff_paths

BASE_FILES = ("src/app.py", "tests/test_app.py", "docs/guide.md")
TARGETS = BASE_FILES


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    for name in BASE_FILES:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")


@st.composite
def _change_sets(draw: st.DrawFn) -> list[tuple[int, str, str]]:
    count = draw(st.integers(min_value=1, max_value=4))
    ops: list[tuple[int, str, str]] = []
    for index in range(count):
        kind = draw(st.sampled_from(["add", "modify", "delete", "rename"]))
        target = draw(st.sampled_from(TARGETS))
        ops.append((index, kind, target))
    return ops


def _apply(repo: Path, ops: list[tuple[int, str, str]]) -> None:
    for index, kind, target in ops:
        path = repo / target
        if kind == "add":
            new = repo / f"src/generated_{index}.py"
            new.parent.mkdir(parents=True, exist_ok=True)
            new.write_text("added = True\n", encoding="utf-8")
        elif kind == "modify" and path.exists():
            path.write_text("value = 2\n", encoding="utf-8")
        elif kind == "delete" and path.exists():
            path.unlink()
        elif kind == "rename" and path.exists():
            path.rename(path.with_suffix(path.suffix + f".renamed{index}"))


def _reported_paths(name_status: str) -> set[str]:
    paths: set[str] = set()
    for line in name_status.splitlines():
        fields = line.split("\t")
        if len(fields) >= 3 and fields[0][:1] in {"R", "C"}:
            paths.update((fields[1], fields[2]))
        elif len(fields) >= 2:
            paths.add(fields[1])
    return paths


@given(ops=_change_sets())
@settings(max_examples=15, deadline=None)
def test_parser_catches_every_path_git_reports(ops: list[tuple[int, str, str]]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        _init_repo(repo)
        _apply(repo, ops)
        _git(repo, "add", "-A")
        unified = _git(repo, "diff", "--cached", "-M").stdout
        name_status = _git(repo, "diff", "--cached", "--name-status", "-M").stdout

        reported = _reported_paths(name_status)
        parsed = set(parse_diff_paths(unified))

        assert reported <= parsed, (
            f"parser missed {reported - parsed} for ops {ops}\n{unified}"
        )
