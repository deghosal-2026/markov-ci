"""Local-LLM repair client (ADR-0011).

Calls any OpenAI-compatible chat-completions endpoint — Ollama, Apple MLX
(``mlx_lm.server``), LM Studio, llama.cpp server, vLLM — using only the Python
standard library, so the core's zero-LLM-SDK guarantee (ADR-0007) holds.

Template ``local-llm`` invokes this module::

    LOCAL_LLM_BASE_URL=http://localhost:11434/v1 \\
    LOCAL_LLM_MODEL=qwen2.5-coder:7b \\
    python3 -m markov_ci.agents.local_llm "<prompt>"

It prints the model's content (which must contain a `````diff`` fence for the
harness parser) followed by a ``tokens_used:`` line.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_TIMEOUT = 300

EXIT_INVALID = 4


def build_payload(*, model: str, prompt: str) -> str:
    """Build the chat-completions request body."""
    return json.dumps(
        {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        },
    )


def parse_response(body: str) -> tuple[str, int]:
    """Extract ``(content, tokens_used)`` from an endpoint response."""
    try:
        data = json.loads(body)
        content = str(data["choices"][0]["message"]["content"])
        usage = data.get("usage") or {}
        tokens = int(
            usage.get("total_tokens")
            or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)),
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"unparseable endpoint response: {exc}") from exc
    return content, tokens


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``python -m markov_ci.agents.local_llm``."""
    parser = argparse.ArgumentParser(
        prog="local_llm",
        description="Send a repair prompt to a local OpenAI-compatible endpoint.",
    )
    parser.add_argument("prompt", help="the repair prompt")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("LOCAL_LLM_BASE_URL", DEFAULT_BASE_URL),
        help="endpoint base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LOCAL_LLM_MODEL", DEFAULT_MODEL),
        help="model name (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("LOCAL_LLM_TIMEOUT", DEFAULT_TIMEOUT)),
        help="request timeout in seconds (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    request = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=build_payload(model=args.model, prompt=args.prompt).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            content, tokens = parse_response(response.read().decode())
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"local_llm: endpoint call failed: {exc}", file=sys.stderr)
        return EXIT_INVALID

    print(content)
    print(f"tokens_used: {tokens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
