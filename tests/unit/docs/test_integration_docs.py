"""M8.4 (#40) — GitLab/Jenkins integration docs (F20)."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "docs" / "how-to" / "integrate-gitlab-jenkins.md"


def _text() -> str:
    return PAGE.read_text(encoding="utf-8")


def test_page_exists() -> None:
    assert PAGE.is_file()


def test_covers_both_platforms() -> None:
    text = _text()
    assert "GitLab CI" in text
    assert "Jenkins" in text


def test_shows_the_full_exit_code_contract() -> None:
    text = _text()
    for code, state in (("0", "a1"), ("2", "a2"), ("3", "a3"), ("4", "invalid")):
        assert f"{code})" in text or f"{code} =" in text, f"missing exit code {code}"
        assert state in text


def test_documents_the_events_artifact_as_recompute_input() -> None:
    text = _text()
    assert "events.jsonl" in text
    assert "recompute" in text


def test_documents_runner_pool_partitioning() -> None:
    text = _text()
    assert "burst" in text.lower()
    assert "runner" in text.lower()


def _fenced(language: str) -> str:
    parts = _text().split("```")
    for part in parts:
        if part.startswith(language + "\n"):
            return part[len(language):]
    raise AssertionError(f"no ```{language} fence found")


def test_gitlab_snippet_is_valid_yaml() -> None:
    parsed = yaml.safe_load(_fenced("yaml"))
    assert "markov-govern" in parsed


def test_jenkins_snippet_uses_a_burst_pool_label() -> None:
    block = _fenced("groovy")
    assert "label" in block
    assert "archiveArtifacts" in block
