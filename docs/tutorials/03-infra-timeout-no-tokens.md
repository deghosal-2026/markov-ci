# Tutorial 03 — Infra timeout, zero tokens

**Demo:** `examples/03-infra-timeout` · **Ships:** v0.1.0 · **Exit code to expect:** `2`

The "don't LLM the outage" story: some failures are *not code*, and the fastest agent
is the one that never runs.

## Run it

```bash
markov-ci run examples/03-infra-timeout/config.yaml \
  --junit examples/03-infra-timeout/report.xml --seed 42
echo $?      # 2 = absorbed in a2_escalate_to_author
```

## What happens, hop by hop

| Hop | State | What occurred |
|---|---|---|
| 1 | `s0 → s1` | tests fail with `TimeoutError` / `ConnectionRefused` signatures |
| 2 | `s1 → a2` | triage classifies `infra_timeout` → **routed directly to escalation** |

Two hops. No `s2`. **`tokens_used: 0`** on every event in the stream.

## Why this routing exists

`infra_timeout` priors are `success: [0.05, 0.01, 0.00]` (spec 0001 §4) — a near-zero
chance an LLM patch fixes a spot-instance interruption or a registry 503. So the
policy gate would reject attempt 1 anyway (0.05 < 0.40); triage simply routes there
directly, skipping even the attempt-1 tokens (spec 0010 §4). `dependency_error`
follows the same route.

You cannot "code-fix" an AWS outage. The article this project builds on called this
out as a pattern; markov-ci enforces it as a rule — deterministic classification
*before* any agent sees anything (principle 5: determinism before intelligence).

## What to notice

- Compare event counts: tutorial 01 emitted 5 events, this one emits 2 — the state
  space itself is the audit trail.
- The developer receives escalation *with the classified context* (which timeout, which
  signature), not a shrug.
- Flip the fixture to a real `AssertionError` and the same config routes to `s2#1` —
  the taxonomy, not luck, decides.
