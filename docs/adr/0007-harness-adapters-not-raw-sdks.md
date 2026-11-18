# ADR-0007: Real agents via headless harness CLIs, never raw model SDKs

**Status:** Accepted
**Date:** 2026-11-16
**Amended by:** [ADR-0016](0016-argv-only-harness-invocation.md) — harness invocation is argv-only (the shell-composition allowance attributed to this ADR is superseded); [ADR-0011](0011-local-llms-via-openai-compatible-endpoints.md) — a minimal, no-tools model adapter under a stdlib client is allowed.

## Context

Research (2026-11): every major coding-agent harness ships a headless/CI mode —
`claude -p` (Claude Code), `opencode run` (OpenCode), `aider --yes-always` — and the
economics are harness-shaped: the same model consumed ~70× more tokens in one harness
than another. Harnesses already solve repo editing, diffing, and session mechanics;
raw SDK adapters would rebuild all of that badly. Meanwhile MCP is becoming the
standard way agents consume external tools (CircleCI, Buildkite, Semaphore all ship
MCP servers).

## Decision

Real-agent support targets **harness CLIs in headless mode** through the same
`AgentAdapter` protocol, plus one generic bring-your-own-command adapter for the long
tail. markov-ci's allowlists, budgets, and caps apply regardless of the harness's own
settings — governance is never delegated. Priors resolve per *(category × adapter)*,
and `adapter` rides on every telemetry event. An MCP server exposing
`analyze`/`validate`/`queue` to agents is the planned inverse direction (PRD F29).

## Considered options

- **Raw model SDKs per provider.** Rejected: rebuilds repo editing, diffing and session
  mechanics badly, and pins a provider dependency into core.
- **A bespoke integration per harness.** Rejected: duplicated glue; the BYO-command
  adapter (T3) covers the long tail instead.
- **Harness CLIs in headless mode behind one protocol (chosen).**

## Consequences

- One thin seam covers Claude Code, OpenCode, Aider, and anything scriptable.
- Core keeps zero LLM/harness SDK dependencies. (The reserved, empty
  `markov-ci[harness]` extra was removed in v0.1.1 — the adapters are in the core.)
- Harness variance becomes measurable (per-harness matrices) instead of folklore.
- We inherit harness CLI churn; contained per-adapter, with contract tests.
- Falsifier: if a major harness deprecates headless mode, the BYO-command adapter
  and community templates (PRD F28) absorb the change.
