# How-to: use a local LLM

> Ships with **M4.5 ([#64](https://github.com/deghosal-2026/markov-ci/issues/64))** ·
> Decision record: [ADR-0011](../adr/0011-local-llms-via-openai-compatible-endpoints.md)

Your model never has to leave the machine. markov-ci's **local-llm** template drives
any OpenAI-compatible endpoint — **Ollama, Apple MLX (`mlx_lm.server`), LM Studio,
llama.cpp server, vLLM** — through a tiny standard-library client. No SDK, no cloud
API key, no data egress: the pipeline, the telemetry, *and* the model all stay local.

## 1. Start your model server

| Server | Command | Endpoint |
|---|---|---|
| **Ollama** | `ollama serve` (and `ollama pull qwen2.5-coder:7b`) | `http://localhost:11434/v1` |
| **Apple MLX** | `pip install mlx-lm && mlx_lm.server --model mlx-community/Qwen2.5-Coder-7B-Instruct-4bit --port 8080` | `http://localhost:8080/v1` |
| **LM Studio** | start the local server (Developer tab) | `http://localhost:1234/v1` |
| **llama.cpp** | `llama-server -m <model.gguf> --port 8080` | `http://localhost:8080/v1` |
| **vLLM** | `vllm serve <model>` | `http://localhost:8000/v1` |

## 2. Point markov-ci at it

```yaml
agent:
  adapter: harness
  harness:
    command_template: 'python3 -m markov_ci.agents.local_llm %PROMPT%'
    timeout_seconds: 300
```

Configure via environment variables (defaults shown):

```bash
export LOCAL_LLM_BASE_URL="http://localhost:11434/v1"   # Ollama's OpenAI port
export LOCAL_LLM_MODEL="qwen2.5-coder:7b"
export LOCAL_LLM_TIMEOUT="300"
markov-ci run --junit report.xml
```

Everything else is unchanged: triage, budgets, caps, allowlists, TMR, the worktree validation,
the isolated `ai-fix/*` branch, and the event stream — full governance, local model.

**Prefer a full harness?** Use the `aider-ollama` template instead:

```yaml
agent:
  adapter: harness
  harness:
    command_template: 'aider --yes-always --model ollama_chat/qwen2.5-coder:7b --message %PROMPT%'
```

## 3. What the client expects

- The endpoint must speak the **OpenAI chat-completions** schema (`POST /chat/completions`).
- The model's reply must contain a ```diff fenced block — that's what the harness
  parser extracts as the patch.
- `tokens_used` comes from the endpoint's `usage` field when it reports one
  (Ollama, MLX, and LM Studio do); otherwise it records 0.
- Governance is **never delegated**: even a local model is allowlisted, budget-capped,
  TMR-checked, and never auto-merged.

## Honest status

The template and client are shipped and conformance-tested offline against stubs
(no network in this repo's CI). Live verification against each server happens at the
v0.2 gate and is recorded in the template's `tested_versions` — consistent with every
other harness template.

## See also

- [Run the examples in Docker](run-in-docker.md) — the rest of the stack, containerized
- [Harness compatibility strategy](../prd/07-harness-compatibility.md) ·
  [spec/0006 § Local model servers](../spec/0006-agent-adapters.md)
