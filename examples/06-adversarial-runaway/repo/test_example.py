from src.example import broken


def test_broken() -> None:
    # the agent's canned patch returns 2; this assertion needs 3, so every
    # proposed patch fails sandbox validation — the demo of per-attempt decay
    assert broken() == 3
