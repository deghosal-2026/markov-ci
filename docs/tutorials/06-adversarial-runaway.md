# Tutorial 06 — Adversarial runaway (termination is a theorem)

**Demo:** `examples/06-adversarial-runaway` · **Ships:** v0.1.0 · **Exit code to expect:** `2`

The strongest guarantee in the product. Hand the pipeline the most hostile prior there is
— `type_mismatch: success = [1.0, 1.0, 1.0]` ("the agent always succeeds") — alongside a
patch that never satisfies the test. The run still terminates.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the sandbox uses git worktrees)
git -C examples/06-adversarial-runaway/repo init -q && \
  git -C examples/06-adversarial-runaway/repo add -A && \
  git -C examples/06-adversarial-runaway/repo commit -qm "demo baseline"

markov-ci run examples/06-adversarial-runaway/config.yaml \
  --junit examples/06-adversarial-runaway/report.xml \
  --repo examples/06-adversarial-runaway/repo --seed 42
echo $?      # 2 = absorbed in a2_escalate_to_author
```

## What happens, hop by hop

| Hop | Transition | Gate outcome |
|---|---|---|
| 1 | `s1 → s2#1` | P(success) = 1.0 ≥ 0.40 → attempt 1 allowed |
| 2 | `s2#1 → s3#1` | patch rejected by the sandbox |
| 3 | `s3#1 → s2#2` | P(success) = 1.0 → attempt 2 allowed |
| 4 | `s2#2 → s3#2` | patch rejected |
| 5 | `s3#2 → s2#3` | P(success) = 1.0 → attempt 3 allowed |
| 6 | `s2#3 → s3#3` | third patch rejected |
| 7 | `s3#3 → a2` | **attempt cap: `attempt = 4 > max_attempts = 3` → escalate** |

Seven events, then `a2_escalate_to_author` (exit `2`). The final hop is the *cap* gate,
not the confidence gate — the priors never decay below the threshold here.

## Why the loop cannot run away

This is the ADR-0004 guarantee made concrete. If the chain were assembled naively,
`success = [1,1,1]` with a permanently-failing patch would be a runaway loop: `I − Q`
singular, `N` undefined, the "infinite retry" incident back. Instead, `max_attempts`
**removes the final loop-back edge at assembly time** and renormalizes that probability
mass into the designed absorbing states. Every chain markov-ci can execute is therefore
absorbing *by construction* — no timeout, no kill script, no budget bleed required to
guarantee termination.

The matrix-level companion of this demo is the property test
`tests/unit/model/test_properties.py::test_adversarial_perfect_success_still_absorbs`;
the end-to-end companion is `tests/e2e/test_adversarial_runaway.py`.

## What to notice

- **Termination is a theorem, not a timeout.** The cap is structural; the run is bounded
  by `max_attempts` no matter what the priors claim.
- **The forecast can be wrong and the guardrail still holds.** `analyze` shows an
  optimistic P(a1) ≈ 0.92, but the actual run is capped at three attempts — the worst
  case is bounded independently of the estimate.
- **Escalation is a designed outcome**, not a crash: exit `2` with the full event trail
  for the reviewer.
