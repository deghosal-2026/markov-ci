# Tutorial 07 — The cheating agent (textbook weakening patterns blocked)

**Demo:** `examples/07-cheating-agent` · **Ships:** v0.1.0 · **Exit code to expect:** `1`

The adversarial agent. Rather than fix the code, the agent proposes a patch that makes
the failing test pass by **deleting its assertion**. markov-ci's test-modification-ratio
(TMR) guardrail hard-stops it before the worktree validation ever runs.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the validation copy uses git worktrees)
git -C examples/07-cheating-agent/repo init -q && \
  git -C examples/07-cheating-agent/repo add -A && \
  git -C examples/07-cheating-agent/repo commit -qm "demo baseline"

markov-ci run examples/07-cheating-agent/config.yaml \
  --junit examples/07-cheating-agent/report.xml \
  --repo examples/07-cheating-agent/repo --seed 42
echo $?      # 1 = absorbed in a2_escalate_to_author
```

The agent is a BYO command adapter (spec 0006 T3): `cheat.py` prints a diff that removes
`assert broken() == 2` from `tests/test_example.py` — a "repair" that would turn a red
test green by weakening it.

## What happens, hop by hop

| Hop | Transition | Gate outcome |
|---|---|---|
| 1 | `s1 → s2#1` | classified `unit_assertion`; the agent proposes a test-weakening diff |
| 2 | `s2#1 → a2` | **TMR hard stop**: 1 assertion deleted → `a2` + `mandatory_review` |

Two events, then `a2_escalate_to_author` (exit `2`). The path allowlist passes
(`tests/**` is writable), so the **TMR** check is what catches the cheat — and it runs
before `s3`, so the worktree validation is never invoked.

## Why this matters

The whole product rests on one assumption: a green suite means something. An agent that
deletes the assertion to make the failure disappear has destroyed the signal — so the
engine treats it as a hard stop, not a warning (spec 0005 §2, ADR-0009). Three triggers
stop a patch:

- any **net assertion deletion**,
- a test-modification **ratio > 1.0** (test lines changed ÷ source lines changed), or
- a **pure test change with no source change**.

On any of them the run escalates to `a2` and sets `mandatory_review`, which the
`RunResult` (and the human output) surfaces for the reviewer. Governance is never
delegated to the harness (principle 7): the check is in the engine, on every proposal.

## What to notice

- **Green still means green.** A patch is not trusted because tests pass; the tests
  themselves are guarded.
- **The stop happens before the worktree validation** — no wasted apply-and-test cycle on a diff
  that was never going to be reviewed as code.
- **`mandatory_review: true`** rides the `RunResult`, so the reviewer sees *why* the run
  escalated, not a shrug.
