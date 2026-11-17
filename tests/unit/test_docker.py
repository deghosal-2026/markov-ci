"""M9.6 (#61) — the Docker runner for the offline examples.

The image pins the interpreter and `git`; Compose runs demos 01-04 under
`--network none` and asserts each documented exit code. These checks are static
(no Docker daemon in CI): they guard the contract in docs/how-to/run-in-docker.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_EXIT_CODES = {"demo-01": "0", "demo-02": "2", "demo-03": "2", "demo-04": "0"}


def test_dockerfile_pins_python_and_installs_git() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in text
    assert "git" in text
    assert "COPY examples /examples" in text


def test_dockerignore_excludes_the_working_tree() -> None:
    text = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert ".git" in text
    assert "tests" in text


def test_compose_runs_every_offline_demo_offline() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert set(services) == set(EXPECTED_EXIT_CODES)
    for name, expected in EXPECTED_EXIT_CODES.items():
        service = services[name]
        assert service["network_mode"] == "none", f"{name} must run offline"
        assert service["entrypoint"][:2] == ["sh", "/examples/run-demo.sh"]
        command = service["command"]
        assert "markov-ci" in command
        assert command[0] == expected, f"{name} must assert exit {expected}"


def test_run_demo_wrapper_exists() -> None:
    assert (ROOT / "examples" / "run-demo.sh").is_file()
