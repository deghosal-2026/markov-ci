"""M0.5 — community health files exist and their links resolve."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_required_files_exist() -> None:
    for name in ("CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md"):
        assert (ROOT / name).is_file(), f"missing {name}"


def test_code_of_conduct_is_contributor_covenant_with_enforcement() -> None:
    text = _read("CODE_OF_CONDUCT.md")
    assert "Contributor Covenant" in text
    assert "Enforcement" in text
    assert "2.1" in text


def test_changelog_follows_keep_a_changelog() -> None:
    text = _read("CHANGELOG.md")
    assert text.lstrip().startswith("# Changelog")
    assert "Keep a Changelog" in text
    assert "Unreleased" in text


def test_readme_local_links_resolve() -> None:
    readme = _read("README.md")
    targets = re.findall(r"\]\(([^)#:]+\.md)\)", readme)
    missing = [t for t in targets if not (ROOT / t).exists()]
    assert missing == [], f"README links to missing files: {missing}"


def test_contributing_and_security_cross_link() -> None:
    assert "SECURITY.md" in _read("CONTRIBUTING.md")
    assert "CONTRIBUTING.md" in _read("SECURITY.md")


# Every user-facing doc the README must point at.
REQUIRED_DOC_LINKS = (
    "docs/OVERVIEW.md",
    "docs/quick-start.md",
    "docs/architecture.md",
    "docs/tutorials/01-lint-error-first-pass.md",
    "docs/tutorials/02-assertion-decay-escalation.md",
    "docs/tutorials/03-infra-timeout-no-tokens.md",
    "docs/tutorials/04-runner-pool-sizing.md",
    "docs/tutorials/05-github-actions-e2e.md",
    "docs/how-to/integrate-github-actions.md",
    "docs/how-to/integrate-gitlab-jenkins.md",
    "docs/how-to/run-in-docker.md",
    "docs/how-to/use-a-local-llm.md",
    "docs/reference/configuration.md",
    "docs/reference/telemetry.md",
    "docs/reference/cli.md",
    "docs/explanations/markov-model.md",
    "docs/explanations/queueing-theory.md",
    "docs/explanations/design-review.md",
    "docs/prd/README.md",
    "docs/spec/README.md",
    "docs/adr/README.md",
    "docs/WBS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "LICENSE",
)


def test_readme_links_every_relevant_doc() -> None:
    readme = _read("README.md")
    missing = [target for target in REQUIRED_DOC_LINKS if f"]({target})" not in readme]
    assert missing == [], f"README is missing links to: {missing}"
