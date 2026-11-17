# Telemetry reference

Normative contract: [spec/0007](../spec/0007-telemetry-events.md) · JSON Schema:
`schemas/transition-event.schema.json` (single source of truth — this page is
generated against it).

One JSON object per line (JSONL), appended + flushed at every state transition — a
killed run leaves a valid partial stream. Telemetry is **local and user-owned**;
markov-ci ships nothing anywhere.

## Event fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | currently `1`; `recompute` accepts all ≤ current |
| `event` | str | v0.1 emits `transition` (one per hop); `absorbed`/`guardrail` are reserved |
| `run_id` | str | UUID per run |
| `commit_sha` | str | head of the run's branch |
| `pr_number` | int \| null | null for local runs |
| `from_state`, `to_state` | str | `name#attempt` form for step-augmented states |
| `duration_ms` | int | time spent in `from_state` |
| `tokens_used` | int | best known; `0` for simulated |
| `failure_category` | str | triage taxonomy (spec 0010) |
| `attempt` | int | 1-based |
| `adapter` | str | `simulated` \| `claude-code` \| `opencode` \| `aider` \| custom |
| `ts` | str | ISO-8601 UTC |

## Example

```json
{"schema_version": 1, "event": "transition", "run_id": "run_8f14e45f",
 "commit_sha": "9f104b6", "pr_number": 42,
 "from_state": "s3_sandbox_validation#1", "to_state": "s2_agent_reasoning#2",
 "duration_ms": 41822, "tokens_used": 18340, "failure_category": "unit_assertion",
 "attempt": 2, "adapter": "simulated", "ts": "2026-11-16T09:41:07Z"}
```

## Guarantees

1. **No secrets ever** — schema-enforced plus a scrub test.
2. **Recomputable.** Events alone rebuild the transition matrix — per *(failure
   category × adapter)*. `adapter` on every event is what makes per-harness matrices
   fall out of `recompute` (the ~70×-token-variance problem, made visible).
3. **Crash-safe.** Append + flush per hop; an absent absorbing state is itself auditable.
4. **On by default.** Telemetry is written to `telemetry.path` unless the config sets
   `telemetry.sink: none`; the run's `events_path` records where it landed.

## Feeding it back

```bash
markov-ci recompute events.jsonl
```

Transition counts → Dirichlet posterior + credible intervals (spec 0002 §2) → a
priors block labeled `source: empirical` you merge back into config. The governance
loop closes itself.
