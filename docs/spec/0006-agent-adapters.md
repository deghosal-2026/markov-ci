# Spec 0006 — Agent adapters

**Status:** Experimental until v0.2 · **Amends:** — · **Implements:** PRD F6, F19

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
sandbox validation (spec 0011) before any state advances.

## 2. SimulatedAgent (default — MUST, v0.1.0)

- Deterministic and seeded; patch fixtures per category so demos run offline with zero
  API keys.
- `id = "simulated"`.
- Calibrated so observed outcomes match the (category × adapter) priors statistically
  (χ² goodness-of-fit within seeded tolerance) — demos reproduce the forecast math.

## 3. HarnessAdapter (SHOULD — v0.2.0, opt-in extras)

These are the adapter tiers defined in PRD 07: protocol-conformant agents
(incl. `SimulatedAgent`) are **T1**; the named harness templates below are **T2**;
the BYO command template is **T3**.

Real agents run through coding-agent **harness CLIs in headless mode**:

| Harness | Headless invocation | Notes |
|---|---|---|
| Claude Code | `claude -p --output-format json "<prompt>"` | tool list narrowed; JSON parsed for token usage |
| OpenCode | `opencode run "<prompt>"` | provider key via secret; no TTY |
| Aider | `aider --yes-always --message "<prompt>"` | git-native, reviewable commits |
| Any other | BYO command template | `agent.harness.command_template` in config (spec 0003) |

Rules:

- markov-ci's allowlists, budgets, and caps apply **regardless of the harness's own
  settings** — governance is never delegated (principles §7).
- Token accounting prefers the harness's reported usage; falls back to per-attempt
  budget estimates.
- Every invocation is bounded by `policy.wall_clock_seconds`.
- Packaging: `pip install markov-ci[harness]`. Core stays importable with zero LLM
  dependencies.
- This repo's CI never exercises a live harness — offline contract tests only.

## 4. Calibration across harnesses

Field data: the same model consumed ~70× more tokens in one harness than another.
Because `adapter` rides on every telemetry event, `recompute` builds per-harness
matrices and priors resolve per *(category × adapter)* (spec 0001 §4) — markov-ci sees
harness economics instead of guessing them.
