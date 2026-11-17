from src.example import broken


def test_broken() -> None:
    assert broken() == 2
