"""#64 — local-LLM client (ADR-0011): OpenAI-compatible endpoint, stdlib only."""

from __future__ import annotations

import json
import urllib.request

import pytest

from markov_ci.agents import TEMPLATES
from markov_ci.agents.local_llm import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    build_payload,
    main,
    parse_response,
)

RESPONSE = {
    "choices": [
        {"message": {"content": "```diff\n--- a/x\n+++ b/x\n@@\n-old\n+new\n```"}},
    ],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
}


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def test_local_templates_are_shipped() -> None:
    assert "local-llm" in TEMPLATES
    assert "aider-ollama" in TEMPLATES
    assert "%PROMPT%" in TEMPLATES["local-llm"].command_template
    assert "ollama" in TEMPLATES["aider-ollama"].command_template


def test_defaults_target_ollama() -> None:
    assert DEFAULT_BASE_URL == "http://localhost:11434/v1"
    assert DEFAULT_MODEL


def test_build_payload_carries_the_prompt() -> None:
    payload = json.loads(build_payload(model="mlx-model", prompt="fix this"))
    assert payload["model"] == "mlx-model"
    assert payload["messages"] == [{"role": "user", "content": "fix this"}]
    assert payload["stream"] is False


def test_parse_response_extracts_content_and_tokens() -> None:
    content, tokens = parse_response(json.dumps(RESPONSE))
    assert "+new" in content
    assert tokens == 120


def test_parse_response_uses_total_tokens_when_present() -> None:
    data = {"choices": [{"message": {"content": "hi"}}], "usage": {"total_tokens": 7}}
    _, tokens = parse_response(json.dumps(data))
    assert tokens == 7


def test_parse_response_tolerates_missing_usage() -> None:
    data = {"choices": [{"message": {"content": "hi"}}]}
    content, tokens = parse_response(json.dumps(data))
    assert content == "hi"
    assert tokens == 0


def test_parse_response_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="unparseable"):
        parse_response("not json at all")


def test_main_calls_the_endpoint_and_prints_result(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["data"] = json.loads(request.data)  # type: ignore[arg-type]
        captured["timeout"] = timeout
        return _FakeResponse(json.dumps(RESPONSE))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    code = main(["--base-url", "http://localhost:8080/v1", "--model", "mlx", "the prompt"])
    out = capsys.readouterr().out
    assert code == 0
    assert captured["url"] == "http://localhost:8080/v1/chat/completions"
    assert captured["data"] == json.loads(build_payload(model="mlx", prompt="the prompt"))
    assert captured["timeout"] == 300
    assert "+new" in out
    assert "tokens_used: 120" in out


def test_main_reads_env_defaults(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("LOCAL_LLM_BASE_URL", "http://localhost:9999/v1")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "qwen:14b")
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["data"] = json.loads(request.data)  # type: ignore[arg-type]
        return _FakeResponse(json.dumps(RESPONSE))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert main(["prompt"]) == 0
    capsys.readouterr()
    assert captured["url"] == "http://localhost:9999/v1/chat/completions"
    assert captured["data"] == json.loads(build_payload(model="qwen:14b", prompt="prompt"))


def test_main_returns_four_on_endpoint_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def boom(request: urllib.request.Request, timeout: int) -> _FakeResponse:
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert main(["prompt"]) == 4
    assert "failed" in capsys.readouterr().err


def test_main_rejects_non_http_schemes_before_any_request(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    called: list[object] = []

    def must_not_run(request: urllib.request.Request, timeout: int) -> _FakeResponse:
        called.append(request)
        raise AssertionError("urlopen must not be reached for a non-http scheme")

    monkeypatch.setattr(urllib.request, "urlopen", must_not_run)
    for scheme in ("file:///etc/passwd", "ftp://host/x", "gopher://host", "data:text/plain,x"):
        assert main(["prompt", "--base-url", scheme]) == 4
        assert "scheme" in capsys.readouterr().err
    assert called == []


def test_main_requires_a_prompt() -> None:
    with pytest.raises(SystemExit):
        main([])
