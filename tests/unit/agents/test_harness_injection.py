"""M13.5 (#89) — adversarial regression suite for argv-only invocation (ADR-0016).

These tests exercise the **real** `_default_runner` (no stub) with a harmless echo
program. Shell metacharacters in the prompt must reach the child verbatim and must
never create a marker file — proof that nothing re-parses the prompt.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from markov_ci.agents.harness import _default_runner, build_argv

# A harmless child that echoes its first argument back on stdout, byte for byte.
_ECHO = (
    f'"{sys.executable}" -c "import sys; sys.stdout.write(sys.argv[1])" %PROMPT%'
)

PAYLOADS = [
    "$(touch {marker})",
    "`touch {marker}`",
    'break"out ; touch {marker} ; echo "x',
    "a; touch {marker}",
    "a | touch {marker}",
    "a && touch {marker}",
    "line1\nline2; touch {marker}",
    "> {marker}",
    "$HOME",
    "'single' \"double\"",
    "$(touch {marker})$(touch {marker})",
    "tab\tand\\backslash\\; touch {marker}",
]


def _expected_prompt(context: str) -> str:
    return f"Fix this unit_assertion failure (attempt 1/3).\n\n{context}"


@pytest.mark.parametrize("payload", PAYLOADS)
def test_payload_reaches_the_child_verbatim_and_is_inert(
    payload: str, tmp_path: Path,
) -> None:
    marker = tmp_path / "pwned"
    prompt = _expected_prompt(payload.replace("{marker}", str(marker)))
    argv = build_argv(_ECHO, prompt)

    completed = _default_runner(argv, timeout=30)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == prompt  # verbatim: no expansion, no escaping
    assert not marker.exists(), "a shell re-parsed the prompt"


def test_the_prompt_is_a_single_argv_element() -> None:
    argv = build_argv(_ECHO, "a b c $(x) `y` ; z")
    assert argv[-1] == "a b c $(x) `y` ; z"


@given(st.text())
@settings(max_examples=200)
def test_parsed_argv_contains_the_prompt_byte_for_byte(text: str) -> None:
    argv = build_argv("harness --msg %PROMPT%", text)
    assert argv == ["harness", "--msg", text]


@given(st.text())
@settings(max_examples=200)
def test_the_prompt_is_never_re_substituted(text: str) -> None:
    # substitution is a single pass over the template: a literal `%PROMPT%`
    # inside the prompt is prompt content, not a placeholder to expand again.
    argv = build_argv("harness --msg %PROMPT%", text)
    assert argv[-1] == text


def test_no_shell_true_and_no_b602_nosec_anywhere_in_src() -> None:
    # M13.6 (#90): bandit guards the subprocess call again — the argv-only
    # invocation means there is no `shell=True` (and no B602 suppression) in src.
    src = Path(__file__).resolve().parents[3] / "src"
    offenders: list[str] = []
    for path in sorted(src.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "shell=True" in text or "nosec B602" in text:
            offenders.append(str(path.relative_to(src)))
    assert offenders == []


