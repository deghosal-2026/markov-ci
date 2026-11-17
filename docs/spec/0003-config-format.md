# Spec 0003 — Configuration format

**Status:** Stable (new keys additive only) · **Amends:** — · **Implements:** PRD F1, F11

## 1. Normative example (default config, abridged)

```yaml
version: 1

states:
  s0_deterministic_verify: { type: transient }
  s1_failure_triage:       { type: transient }
  s2_agent_reasoning:      { type: transient, loop_capable: true }
  s3_sandbox_validation:   { type: transient, loop_capable: true }
  s4_regression_check:     { type: transient }
  a1_ready_for_human_review: { type: absorbing }
  a2_escalate_to_author:     { type: absorbing }
  a3_budget_exceeded:        { type: absorbing }

transitions:
  - { from: s0_deterministic_verify, to: a1_ready_for_human_review, probability: 0.82 }
  - { from: s0_deterministic_verify, to: s1_failure_triage,        probability: 0.18 }
  - { from: s1_failure_triage,       to: s2_agent_reasoning,       probability: 0.75 }
  - { from: s1_failure_triage,       to: a2_escalate_to_author,    probability: 0.25 }
  # the agent's patch is only as likely as the prior for the category
  - { from: s2_agent_reasoning,      to: s3_sandbox_validation,    prior_driven: true, per_attempt: true }
  - { from: s3_sandbox_validation,   to: s4_regression_check,      probability: 0.65 }
  - { from: s3_sandbox_validation,   to: s2_agent_reasoning,       probability: 0.25, per_attempt: true }
  - { from: s3_sandbox_validation,   to: a2_escalate_to_author,    probability: 0.10 }
  - { from: s4_regression_check,    to: a1_ready_for_human_review, probability: 0.90 }
  - { from: s4_regression_check,     to: a2_escalate_to_author,    probability: 0.10 }

policy:
  min_confidence: 0.40
  max_attempts: 3
  max_tokens: 200000
  wall_clock_seconds: 900

priors:
  default:
    lint_error:     { success: [0.92, 0.65, 0.20], cost_weight: 1.0, source: prior }
    type_mismatch:  { success: [0.85, 0.55, 0.25], cost_weight: 1.5, source: prior }
    unit_assertion: { success: [0.74, 0.45, 0.15], cost_weight: 2.5, source: prior }
    infra_timeout:  { success: [0.05, 0.01, 0.00], cost_weight: 5.0, source: prior }

agent:
  adapter: simulated            # simulated | harness (BYO command via harness.command_template)
  allow_write: ["src/**", "tests/**"]
  deny_write: []                # the always-denied set applies regardless (spec 0005)
  harness:                      # used when adapter: harness (spec 0006)
    command_template: 'claude -p --output-format json "%PROMPT%"'
    timeout_seconds: 300

telemetry:
  sink: file
  path: .markov-ci/events.jsonl
```

## 2. Validation rules (enforced by the loader; pydantic ≥ 2)

1. `version` must be `1`.
2. Unknown keys are **rejected** (fail loudly, never silently ignored).
3. Every state referenced by a transition must exist; types must match edge direction
   (no edges may leave an absorbing state).
4. `s2#k → s3#k` edges are generated from priors — declaring them statically is an error.
5. `per_attempt: true` edges require a matching prior (they consume `success[k]`).
6. Row sums are validated after assembly (spec 0002 §1.4), not at parse time.
7. `priors` must resolve for every (adapter, category) pair actually used.
8. A `prior_driven: true` edge **must not** set `probability` — its probability comes
   from `priors[adapter][category].success[k]`. Such an edge must also be
   `per_attempt: true`. (This is how `s2 -> s3` is expressed.)

## 3. Conventions

- **Escalation sink.** Any remainder probability in a transient row is routed to the
  *escalation* absorbing state — the absorbing state whose id names escalation
  (`a2_escalate_to_author`); if none matches, the first absorbing state. This is what
  produces `s2#k -> a2 = 1 - success[k]` and the final-attempt renormalization
  (spec 0002 §1.3).
- **Default category.** When a command is run without `--category`, the category
  `default` is used. The packaged config ships a `default` curve
  (spec 0001 §4) so the worked example reproduces with zero configuration.

## 4. Defaults

The packaged default (above) ships in the wheel (`markov_ci.data.default`) so that
zero-config `analyze` and `validate` work out of the box (PRD F11). User configs may
override any subset; merged configs are re-validated as a whole.
