# Spec 0006 — Agent adapters

**Status:** Experimental until v0.2 · **Amends:** ADR-0007 (invocation is argv-only, ADR-0016) · **Implements:** PRD F6, F19

markov-ci governs agents; it never hosts them. Every agent — simulated or real — is
reached through one protocol. See ADR-0007 for why real agents target harness CLIs
rather than raw model SDKs.

## 1. Protocol

```python
class AgentAdapter(Protocol):
    id: str   # recorded on every telemetry event (spec 0007)

    def repair(self, ctx: RepairContext) -> PatchProposal: ...
```

- `RepairContext`: failure category, minimized logs (spec 0010), git diff, repo rules,
  attempt number. **Never** raw 50k-line logs.
- `PatchProposal`: unified diff + rationale + token usage (best known; 0 if unknown).

The engine never trusts the adapter: every proposal passes guardrails (spec 0005) and
worktree validation (spec 0011) before any state advances.

## 2. SimulatedAgent (default — MUST, v0.1.0)

- Deterministic and seeded; patch fixtures per category so demos run offline with zero
  API keys.
- `id = "simulated"`.
- Calibrated so observed outcomes match the (category × adapter) priors statistically
  (χ² goodness-of-fit within seeded tolerance) — demos reproduce the forecast math.

## 3. HarnessAdapter (SHOULD — opt-in extra; shipped alongside v0.1.0)

These are the adapter tiers defined in PRD 07: protocol-conformant agents
(incl. `SimulatedAgent`) are **T1**; the named harness templates below are **T2**;
the BYO command template is **T3**.

Real agents run through coding-agent **harness CLIs in headless mode**:

### Invocation contract — argv-only (ADR-0016)

`command_template` is split with `shlex.split` **before** `%PROMPT%` is substituted; the
prompt becomes **one argv element** and the process runs with `shell=False`. No shell
re-parses the prompt, so `$(…)`, backticks, `;`, `|`, `&&`, newlines, `$HOME` and quotes
reach the child verbatim:

- Do **not** quote `%PROMPT%`, and do **not** rely on shell composition (pipes, globs) in
  a template — write a wrapper script instead.
- Templates that re-enter a shell with the prompt (`sh` / `bash` / `zsh` / `dash` /
  `pwsh` / `powershell` / `cmd` with `%PROMPT%` after `-c` / `/c`) are rejected; the safe
  positional form `bash -c 'tool "$1"' _ %PROMPT%` is allowed.
- Templates are validated at config load (empty, unbalanced quotes, missing `%PROMPT%`,
  `%PROMPT%` as the program name) — invalid config, exit **4**.
- `%PROMPT_FILE%` (a `0600` temp file) or stdin keeps long prompts off `ps` / ARG_MAX.

| Harness | Headless invocation | Notes |
|---|---|---|
| Claude Code | `claude -p --output-format json %PROMPT%` | tool list narrowed; JSON parsed for token usage |
| OpenCode | `opencode run %PROMPT%` | provider key via secret; no TTY |
| Aider | `aider --yes-always --message %PROMPT%` | git-native, reviewable commits |
| Local — any OpenAI-compatible endpoint (Ollama, MLX, LM Studio, llama.cpp, vLLM) | `python3 -m markov_ci.agents.local_llm %PROMPT%` | stdlib-only client; tokens from endpoint `usage` (ADR-0011) |
| Aider + Ollama | `aider --yes-always --model ollama_chat/<model> --message %PROMPT%` | full harness on a local model |
| Any other | BYO command template | `agent.harness.command_template` in config (spec 0003) |

### Local model servers (ADR-0011)

`local-llm` targets **any OpenAI-compatible** chat-completions endpoint via a
stdlib-only client — no SDK. Configuration is environment-driven:

| Variable | Default | Meaning |
|---|---|---|
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | endpoint base (Ollama's OpenAI port) |

> Point `LOCAL_LLM_BASE_URL` at a non-loopback host and prompts leave the machine; the
> "nothing leaves your machine" claim holds only for a loopback endpoint (ADR-0011).
| `LOCAL_LLM_MODEL` | `qwen2.5-coder:7b` | model name |
| `LOCAL_LLM_TIMEOUT` | `300` | request timeout (seconds) |

Known-good servers: **Ollama** (`ollama serve` → `:11434/v1`), **Apple MLX**
(`mlx_lm.server --model <model> --port 8080`), **LM Studio** (local server),
**llama.cpp** (`llama-server`), **vLLM**. The model's reply must contain a
```diff fence for the harness parser; tokens come from the endpoint's `usage`
when it reports one.

Rules:

- markov-ci's allowlists, budgets, and caps apply **regardless of the harness's own
  settings** — governance is never delegated (principles §7).
- Token accounting prefers the harness's reported usage; falls back to per-attempt
  budget estimates.
- Every invocation is bounded by `policy.wall_clock_seconds`.
- Packaging: `pip install markov-ci`. Core stays importable with zero LLM
  dependencies.
- This repo's CI never exercises a live harness — offline contract tests only.
- Each template records the harness CLI version it was authored/verified against
  (`tested_versions`). Until a maintainer runs it against a live CLI it is marked
  `unverified`; live verification is deliberately out of this repo's CI (spec 0012 §4).

## 4. Calibration across harnesses

Field data: the same model consumed ~70× more tokens in one harness than another.
Because `adapter` rides on every telemetry event, `recompute` builds per-harness
matrices and priors resolve per *(category × adapter)* (spec 0001 §4) — markov-ci sees
harness economics instead of guessing them.
