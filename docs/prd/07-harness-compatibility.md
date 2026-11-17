# 07 — Harness compatibility strategy

**Implements:** F6, F19, F28, F29 · **Decision record:** [ADR-0007](../adr/0007-harness-adapters-not-raw-sdks.md)

## 1. Why harness compatibility is a product pillar

- Every major coding-agent **harness ships a headless/CI mode**: `claude -p`
  (Claude Code), `opencode run` (OpenCode), `aider --yes-always` (Aider), Codex CLI,
  Goose, OpenHands. Adoption happens through these — not through raw model SDKs.
- **The economics are harness-shaped:** the same model has been observed consuming ~70×
  more tokens in one harness than another. Transition probabilities and cost per attempt
  are therefore per-harness quantities; a governance tool that can't see the harness is
  blind to the biggest variable in the system.
- **MCP is the emerging seam** for agents consuming external tools (CircleCI, Buildkite,
  Semaphore, TeamCity all ship MCP servers). Governance belongs on both sides of that
  seam.

## 2. What "compatible" means — three tiers

| Tier | Meaning | Ships |
|---|---|---|
| **T1 — Protocol-conformant** | Any agent implementing `AgentAdapter.repair(ctx) -> PatchProposal` runs under full governance | v0.1.0 (simulated agent proves the seam) |
| **T2 — Verified harness template** | markov-ci ships + tests a headless invocation pattern for a named harness, with token accounting and timeout enforcement | v0.2.0: Claude Code, OpenCode, Aider, **local-llm**, **aider-ollama** |
| **T3 — BYO command** | Generic `command_template` adapter: any CLI that takes a prompt and produces a diff | v0.2.0 |

## 3. Supported harness matrix

| Harness | Tier | Invocation (contract) | Token accounting | Status |
|---|---|---|---|---|
| SimulatedAgent | T1 | in-process, seeded | exact (0) | v0.1.0 MUST |
| Claude Code | T2 | `claude -p --output-format json "<prompt>"` | from JSON stream | v0.2.0 |
| OpenCode | T2 | `opencode run "<prompt>"` | provider-reported, else estimate | v0.2.0 |
| Aider | T2 | `aider --yes-always --message "<prompt>"` | commit-based estimate | v0.2.0 |
| **Local model servers** (Ollama, Apple MLX, LM Studio, llama.cpp, vLLM) | T2 | `python3 -m markov_ci.agents.local_llm "%PROMPT%"` — any OpenAI-compatible endpoint (ADR-0011) | endpoint `usage` when reported | v0.2.0 (#64) |
| Aider + Ollama | T2 | `aider --yes-always --model ollama_chat/<model> --message "%PROMPT%"` | commit-based estimate | v0.2.0 (#64) |
| Codex CLI, Goose, OpenHands | T2/T3 | community templates (F28) | varies | v0.3.0 backlog |
| Anything else | T3 | user-supplied `command_template` | estimate | v0.2.0 |

## 4. Compatibility requirements (binding)

1. **Governance never delegated.** markov-ci's allowlists, budgets, caps, and TMR
   checks apply regardless of the harness's own settings. Harness allowlists are
   additive defense, never a substitute. A harness's "auto-accept everything" mode
   changes nothing inside markov-ci.
2. **No SDK in core.** Core is importable with zero LLM/harness dependencies;
   T2 adapters live in the `markov-ci[harness]` extra; contract tests run offline.
3. **Every invocation bounded.** `policy.wall_clock_seconds` wraps every harness call;
   a hung harness absorbs into `a3`, never hangs the pipeline.
4. **Token accounting, best effort but explicit.** Prefer harness-reported usage;
   otherwise label the estimate as such in telemetry. Forecasts state which they used.
5. **Per-harness priors.** Priors resolve by *(category × adapter)* with `default`
   fallback (spec 0001 §4); `adapter` rides on every event; `recompute` builds
   per-harness matrices (CUJ-4).
6. **Version pinning & tolerance.** T2 templates declare the tested harness CLI
   versions; minor-version drift tolerated, breaking changes → template fix + changelog
   entry. Never silently break a customer's harness.
7. **Conformance suite.** One suite, run against simulated + every T2 adapter: same
   fixtures, same expected absorbing states. A harness adapter ships only if the suite
   is green offline.

## 5. The inverse direction — MCP governance server (F29, COULD/v0.3+)

Expose `analyze`, `validate`, `queue` as MCP tools so **any agent can query the
governance model before acting** ("is another retry worth it? what's my budget head
room?"). Mirrors the CircleCI/Buildkite MCP pattern but for governance, not pipeline
data. Requires F3, F16. This turns markov-ci into a tool agents themselves consult —
the harness story cuts both ways.

## 6. Anti-requirements (what compatibility must never become)

- ❌ Not a harness: no prompting, planning, or model calling inside markov-ci.
- ❌ Not auto-merge: `a1` remains terminal regardless of harness capability.
- ❌ Not trust-by-default: a harness's own safety settings are never accepted as
  evidence of compliance — conformance tests are.
