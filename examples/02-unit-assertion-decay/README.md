# Example 02 — unit-assertion decay → escalation

**Ships:** v0.1.0 · **Exit code to expect:** `2` · **Tutorial:** [02 — decay → escalate](../../docs/tutorials/02-assertion-decay-escalation.md)

A harder failure: the agent proposes a patch that does not resolve the assertion, the
per-attempt success prior decays, and the confidence gate escalates to a human **before**
the third attempt is spent. Offline, deterministic, zero API keys.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the sandbox uses git worktrees)
git -C examples/02-unit-assertion-decay/repo init -q && \
  git -C examples/02-unit-assertion-decay/repo add -A && \
  git -C examples/02-unit-assertion-decay/repo commit -qm "demo baseline"

markov-ci run examples/02-unit-assertion-decay/config.yaml \
  --junit examples/02-unit-assertion-decay/report.xml \
  --repo examples/02-unit-assertion-decay/repo --seed 42
echo $?    # 2 = absorbed in a2_escalate_to_author
```

## Expected event stream

Five events (`.markov-ci/events.jsonl`), every one carrying
`failure_category: unit_assertion`, `adapter: simulated`:

| Hop | Transition | Gate outcome |
|---|---|---|
| 1 | `s1_failure_triage → s2_agent_reasoning#1` | classified `unit_assertion`; P(success) = **0.74** ≥ 0.40 → attempt 1 allowed |
| 2 | `s2_agent_reasoning#1 → s3_sandbox_validation#1` | patch proposed — sandbox says it did **not** fix the assertion |
| 3 | `s3_sandbox_validation#1 → s2_agent_reasoning#2` | loop back with the new error logs; P(success) = **0.45** ≥ 0.40 → attempt 2 allowed |
| 4 | `s2_agent_reasoning#2 → s3_sandbox_validation#2` | second patch — sandbox rejects again |
| 5 | `s3_sandbox_validation#2 → a2_escalate_to_author` | attempt 3 would carry P(success) = **0.15** < 0.40 → **confidence gate: escalate** |

Absorbed in `a2_escalate_to_author` — the developer gets the diagnostic context and the
full event trail; zero mystery, zero third-attempt spend.

## What this proves

**The stop is a policy decision, not a crash.** The run does not retry until a timer
kills it or the budget bleeds dry: the decaying prior (`0.74 → 0.45 → 0.15`) crosses the
`min_confidence` threshold (`0.40`), and the gate routes to a *designed* absorbing state
with exit code `2` and a complete event trail. Attempt 3 is never attempted. Escalation
is a first-class outcome, and `recompute` can later learn from both failed hops.

## Forecast vs. actual

`markov-ci analyze --category unit_assertion` predicts, from the priors alone:

| Quantity | `analyze` forecast | this seeded run |
|---|---|---|
| P(absorbed in `a1`) | 0.885 | 0.0 (both patches rejected) |
| P(absorbed in `a2`) | 0.115 | 1.0 (escalated) |
| expected steps to absorption | 1.527 | 2 attempts made, then the gate stops |
| expected cost (cost_weight units) | 1.527 | 2.0 realized (unit weights) |

**The expected-token math.** `unit_assertion` carries `cost_weight: 2.5` (spec 0001 §4),
so attempt 3 is the most expensive hop in the pipeline *and* the least likely to succeed
(P = 0.15). The gate spends two attempts and refuses the third — the number that ends the
"one more retry?" debate. With the default `SimulatedAgent` the token count is `0`
(offline); the saved third attempt is the real currency here. Lower `min_confidence` to
`0.10` and `analyze` shows what that third attempt would cost you — that comparison *is*
the debate, ended with a number (CUJ-1).
