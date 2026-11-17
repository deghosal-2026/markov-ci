"""M0.6 — the docs site is configured and builds in CI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MKDOCS = ROOT / "mkdocs.yml"
DOCS_WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"

PLANNING_PREFIXES = ("prd/", "spec/", "adr/", "WBS")


def _config() -> dict[str, Any]:
    return yaml.safe_load(MKDOCS.read_text(encoding="utf-8"))


def _nav_files(node: Any) -> list[str]:
    """Flatten a mkdocs nav structure to its `.md` targets."""
    found: list[str] = []
    if isinstance(node, str):
        if node.endswith(".md"):
            found.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            found.extend(_nav_files(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_nav_files(item))
    return found


def test_mkdocs_config_exists() -> None:
    assert MKDOCS.is_file()


def test_theme_is_material() -> None:
    assert _config()["theme"]["name"] == "material"


def test_every_nav_target_exists_and_is_not_planning_doc() -> None:
    nav = _nav_files(_config()["nav"])
    assert nav, "nav is empty"
    missing = [f for f in nav if not (ROOT / "docs" / f).is_file()]
    assert missing == [], f"nav points at missing files: {missing}"
    leaked = [f for f in nav if f.startswith(PLANNING_PREFIXES)]
    assert leaked == [], f"planning docs must stay out of the site nav: {leaked}"


def test_docs_workflow_exists_and_builds_strict() -> None:
    assert DOCS_WORKFLOW.is_file()
    text = DOCS_WORKFLOW.read_text(encoding="utf-8")
    assert "mkdocs build --strict" in text


def test_docs_workflow_triggers_on_docs_changes() -> None:
    text = DOCS_WORKFLOW.read_text(encoding="utf-8")
    assert "docs/**" in text and "mkdocs.yml" in text
