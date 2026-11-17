# Example 07 — the cheating agent (green still means green)

**Ships:** v0.1.0 · **Exit code to expect:** `2` · **Tutorial:** [07 — cheating agent](../../docs/tutorials/07-cheating-agent.md)

The adversarial agent. Instead of fixing the code, the agent proposes a patch that makes
the failing test "pass" by **deleting its assertion** — the project's anti-pattern #1.
The TMR (test-modification-ratio) guardrail hard-stops it *before the sandbox ever runs*,
escalates to `a2`, and raises `mandatory_review`. Green still means green.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the sandbox uses git worktrees)
git -C examples/07-cheating-agent/repo init -q && \
  git -C examples/07-cheating-agent/repo add -A && \
  git -C examples/07-cheating-agent/repo commit -qm "demo baseline"

markov-ci run examples/07-cheating-agent/config.yaml \
  --junit examples/07-cheating-agent/report.xml \
  --repo examples/07-cheating-agent/repo --seed 42
echo $?      # 2 = absorbed in a2_escalate_to_author
```

The agent is a BYO command adapter (spec 0006 T3): `cheat.py` prints a diff that removes
`assert broken() == 2` from `tests/test_example.py`.

## Expected output

```
absorbed: a2_escalate_to_author · tokens 0 · 20 ms · branch ai-fix/local-<run_id>
mandatory review: test-weakening guardrail tripped — 1 assertion(s) deleted; pure test change with no source change
```

Two events (`.markov-ci/events.jsonl`), `failure_category: unit_assertion`,
`adapter: harness`:

| Hop | Transition | What occurred |
|---|---|---|
| 1 | `s1_failure_triage → s2_agent_reasoning#1` | triage classifies `unit_assertion`; the agent proposes a test-weakening diff |
| 2 | `s2_agent_reasoning#1 → a2_escalate_to_author` | **TMR hard stop** — 1 assertion deleted → `a2` + `mandatory_review` |

The sandbox is never reached: `visits` shows `s2#1 → a2`, no `s3`.

## What this proves

**Green still means green.** A passing test suite is only evidence if the assertions are
real. The moment a patch *removes* an assertion (or the diff is test-heavy, or pure test
with no source change), the engine stops the run and flags it for a human — it never
trusts the agent's word that the suite passed. This is guardrail-as-code (principle 3):
the check runs in the engine, on every proposal, regardless of the adapter or the
harness's own safety settings. The reviewer gets `mandatory_review: true` in the
`RunResult` and the exact reason, not a silently weakened suite.

## Forecast vs. actual

`markov-ci analyze --category unit_assertion` predicts a *healthy* pipeline:

| Quantity | `analyze` forecast | this seeded run |
|---|---|---|
| P(absorbed in `a1`) | 0.885 | 0.0 (patch rejected by guardrails) |
| P(absorbed in `a2`) | 0.115 | 1.0 (`mandatory_review`) |
| attempts before absorption | ≤ 3 | 1 (stopped before the sandbox) |
| tokens spent | — | 0 |

The forecast describes a well-behaved agent. The demo is the **adversarial** one: the
math says "likely fine", the guardrail says "this patch weakens your tests" — and the
guardrail wins. The suite's integrity does not depend on the agent's honesty.
