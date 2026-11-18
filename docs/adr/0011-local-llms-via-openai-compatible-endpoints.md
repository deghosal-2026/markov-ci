# ADR-0011: Local LLMs via OpenAI-compatible endpoints, never a new SDK

**Status:** Accepted
**Date:** 2026-11-16
**Amends:** ADR-0007 — allows a minimal, **no-tools** model adapter (a stdlib client), which ADR-0007's "never raw SDKs" rule would otherwise forbid. It is not a harness: no repo tools, no session, no diff loop beyond the prompt's ```diff fence.

## Context

Users increasingly run local models (Ollama, Apple MLX, LM Studio, llama.cpp server,
vLLM) for privacy and cost. For markov-ci this is a perfect fit: the pipeline, the
events, and now the model itself can all stay on one machine. ADR-0007 routes real
agents through harness CLIs — but a local stack may have no harness CLI at all, just
a model server.

## Decision

Local LLMs plug in through three existing seams, with **no new dependency**:

1. **T2 template `local-llm`** — wraps a tiny standard-library-only client
   (`python -m markov_ci.agents.local_llm`) that POSTs the repair prompt to any
   OpenAI-compatible `/v1/chat/completions` endpoint and prints the content plus a
   `tokens_used:` line the harness parser understands. Config via
   `LOCAL_LLM_BASE_URL` (default `http://localhost:11434/v1`), `LOCAL_LLM_MODEL`,
   `LOCAL_LLM_TIMEOUT`.
2. **T2 template `aider-ollama`** — the Aider harness configured for Ollama, for
   users who want a full harness on a local model.
3. **T3 BYO command** — unchanged; any local CLI works.

The client uses `urllib` (stdlib), so the zero-LLM-SDK guarantee enforced by
`test_core_has_no_llm_or_harness_sdk` holds. Unit tests stub `urlopen` — no network
in CI, no skipped tests. Token accounting uses the endpoint's `usage` when present.

## Considered options

- **A new SDK per local server** (`ollama-python`, `llama-cpp-python`, …). Rejected:
  breaks the zero-LLM-SDK guarantee and multiplies dependencies.
- **Shell out to each server's own CLI.** Rejected: no common schema; token accounting and
  the ```diff contract would differ per server.
- **OpenAI-compatible HTTP through a stdlib client (chosen).**

## Consequences

- "Nothing leaves your machine" is true **by default** and enforced only while
  `LOCAL_LLM_BASE_URL` is loopback — pointed at any other host, prompts leave the machine
  (spec 0006 §3).
- The response must contain a ```diff fence for the harness parser — documented in
  the template and the how-to.
- Live verification of local endpoints remains maintainer-run (templates ship
  `tested_versions: "unverified"` until the v0.2 gate) — CI stays offline.
- **Falsifier:** if local endpoints diverge from the OpenAI schema in practice,
  extend `parse_response` rather than adding a server-specific SDK.
