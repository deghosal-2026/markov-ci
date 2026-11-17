# Configuration reference

Normative contract: [spec/0003](../spec/0003-config-format.md). The loader is
pydantic-validated; unknown keys are rejected with line numbers — never silently
ignored. Default config: spec 0003 §1 (packaged as `markov_ci.data.default`).

## Top-level keys

| Key | Type | Notes |
|---|---|---|
| `version` | int | must be `1` |
| `states` | map | state ID → `{type: transient \| absorbing, loop_capable?: bool}` |
| `transitions` | list | edges (below) |
| `policy` | map | gates (below) |
| `priors` | map | `default` + per-adapter blocks (below) |
| `agent` | map | adapter selection + allowlists |
| `telemetry` | map | sink + path |

## `transitions` entries

| Field | Type | Notes |
|---|---|---|
| `from`, `to` | state ID | must exist; **no edges may leave an absorbing state** |
| `probability` | float | static edge probability |
| `per_attempt` | bool | `true` = this edge consumes `priors[adapter][category].success[k]` on attempt `k` |

The `s2#k → s3#k` and loop-back edges are *generated* from priors and `max_attempts`
— declaring them statically is a validation error.

## `policy`

| Field | Default | Meaning |
|---|---|---|
| `min_confidence` | `0.40` | reject an attempt whose P(success) falls below |
| `max_attempts` | `3` | step cap — also drives step augmentation and the absorption guarantee |
| `max_tokens` | `200000` | absorbing `a3` if exceeded |
| `wall_clock_seconds` | `900` | absorbing `a3` if exceeded |

Gates evaluate strictly in order: **budget → cap → confidence** (spec 0004).

## `priors`

Keyed by *(adapter → category)*, with `default` as fallback:

```yaml
priors:
  default:                                  # adapter "*" — shipped conservative priors
    lint_error:     { success: [0.92, 0.65, 0.20], cost_weight: 1.0, source: prior }
    type_mismatch:  { success: [0.85, 0.55, 0.25], cost_weight: 1.5, source: prior }
    unit_assertion: { success: [0.74, 0.45, 0.15], cost_weight: 2.5, source: prior }
    infra_timeout:  { success: [0.05, 0.01, 0.00], cost_weight: 5.0, source: prior }
  claude-code:                              # adapter-specific once telemetry exists
    unit_assertion: { success: [0.71, 0.42, 0.12], cost_weight: 3.1, source: empirical }
```

- Resolution: `priors[adapter][category]` → `priors.default[category]` → error.
- `success[k]` = P(patch valid on attempt k); `cost_weight` scales the per-state cost
  vector behind `C = N·c`.
- `source: prior | empirical` is **required** — `recompute` writes `empirical`
  (spec 0007 §4); cold start runs on labeled priors, never on false confidence.

## `agent`

```yaml
agent:
  adapter: simulated            # simulated | harness (BYO command via harness.command_template)
  allow_write: ["src/**", "tests/**"]
  deny_write: []                # informational — the always-denied set applies regardless
  harness:
    command_template: 'claude -p --output-format json "%PROMPT%"'
    timeout_seconds: 300
```

**Always-denied regardless of config** (cannot be widened): `.github/**`, `.git`,
`*.env`, `**/secrets/**`, CI configs, lockfiles, `LICENSE` (spec 0005 §1).
Harness adapters ship as `pip install markov-ci[harness]` (ADR-0007); the simulated
agent needs nothing.

## `telemetry`

```yaml
telemetry:
  sink: file
  path: .markov-ci/events.jsonl
```

Local JSONL only — markov-ci phones home to no one. Disabling telemetry is the
explicit `telemetry.sink: none` setting (spec 0007 §3); there is no CLI flag for it.
