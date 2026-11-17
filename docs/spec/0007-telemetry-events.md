# Spec 0007 — Telemetry events

**Status:** Stable (changes guarded by `schema_version`) · **Implements:** PRD F9

## 1. Contract

One JSON object per line (JSONL), emitted at every state transition; append + flush —
a killed run leaves a valid partial stream. JSON Schema lives at
`schemas/transition-event.schema.json` (single source of truth; the reference page is
generated against it).

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | currently `1` |
| `event` | str | `transition` \| `absorbed` \| `guardrail` |
| `run_id` | str | UUID per run |
| `commit_sha` | str | head of the run's branch |
| `pr_number` | int \| null | null for local runs |
| `from_state`, `to_state` | str | `name#attempt` form for augmented states |
| `duration_ms` | int | time in `from_state` |
| `tokens_used` | int | best known; 0 for simulated |
| `failure_category` | str | taxonomy from spec 0010 |
| `attempt` | int | 1-based |
| `adapter` | str | `simulated` \| `claude-code` \| `opencode` \| `aider` \| custom name |
| `ts` | str | ISO-8601 UTC |

## 2. Example

```json
{"schema_version": 1, "event": "transition", "run_id": "run_8f14e45f",
 "commit_sha": "9f104b6", "pr_number": 42,
 "from_state": "s3_sandbox_validation#1", "to_state": "s2_agent_reasoning#2",
 "duration_ms": 41822, "tokens_used": 18340, "failure_category": "unit_assertion",
 "attempt": 2, "adapter": "simulated", "ts": "2026-11-16T09:41:07Z"}
```

## 3. Rules

- **No secrets ever** — schema validation plus a scrub check in tests.
- Events alone are sufficient to recompute the matrix, per *(category × adapter)*.
- Telemetry is on by default (`telemetry.path`); the only way to disable it is the
  explicit `telemetry.sink: none` config, and the run's `events_path` then records the
  absence.

## 4. Recompute

`markov-ci recompute events.jsonl` → transition counts per (category, adapter) →
Dirichlet posterior + credible intervals (spec 0002 §2) → a priors block labeled
`source: empirical` (spec 0003 §1) that can be merged back into config. The matrix is
learnable; the governance loop closes itself.
