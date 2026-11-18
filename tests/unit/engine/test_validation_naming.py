"""M13.13 (#97) — retire the word "sandbox" (ADR-0012); name the step worktree validation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_the_engine_exposes_worktree_validation_names() -> None:
    from markov_ci.engine import ValidationResult, WorktreeValidator

    assert WorktreeValidator.__name__ == "WorktreeValidator"
    assert ValidationResult.__name__ == "ValidationResult"


def test_the_validation_module_is_named_for_what_it_does() -> None:
    import markov_ci.engine.validation as validation

    assert validation.__name__ == "markov_ci.engine.validation"


def test_user_facing_text_does_not_say_sandbox() -> None:
    for relative in ("README.md", "action.yml"):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        assert "sandbox" not in text, f"{relative} still says 'sandbox'"
