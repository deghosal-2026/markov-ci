"""M12.20 (#84) — docs version-reference test.

No `uses:` line may reference a version greater than ``project.version`` — a doc or
workflow that points at an unreleased ref is wrong (a copy-paste example that cannot
work). Only references to this project's own Action are checked.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_CURRENT = tuple(int(part) for part in tomllib.loads(
    (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
)["project"]["version"].split(".")[:3])

_USE = re.compile(r"uses:\s*([^\s@]+)@v(\d+)\.(\d+)\.(\d+)")


def _files() -> list[Path]:
    return [
        *sorted((ROOT / ".github" / "workflows").glob("*.yml")),
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "examples").rglob("*.md")),
        *sorted((ROOT / "examples").rglob("*.yml")),
        *sorted((ROOT / "examples").rglob("*.yaml")),
        ROOT / "README.md",
        ROOT / "action.yml",
    ]


def test_no_uses_line_references_a_future_version() -> None:
    offenders: list[str] = []
    references = 0
    for path in _files():
        for owner_repo, major, minor, patch in _USE.findall(
            path.read_text(encoding="utf-8"),
        ):
            if "markov-ci" not in owner_repo:
                continue
            references += 1
            referenced = (int(major), int(minor), int(patch))
            if referenced > _CURRENT:
                version = ".".join(str(part) for part in referenced)
                offenders.append(f"{path.relative_to(ROOT)}: {owner_repo}@v{version}")
    assert offenders == [], f"uses: lines reference a future version: {offenders}"
    assert references > 0, "expected at least one reference to the markov-ci Action"
