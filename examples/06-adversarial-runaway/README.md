# Example 06 — adversarial runaway (termination is a theorem)

**Ships:** v0.1.0 · **Exit code to expect:** `1` · **Tutorial:** [06 — adversarial runaway](../../docs/tutorials/06-adversarial-runaway.md)

The strongest guarantee in the product. Give the pipeline the most hostile prior there
is — `type_mismatch: success = [1.0, 1.0, 1.0]`, i.e. "the agent always succeeds" — and a
patch that never satisfies the test. The run still terminates: the attempt cap removes
the final loop-back edge at assembly time, so absorption is **structural, not
procedural**. No timeout, no kill script, no budget bleed.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the sandbox uses git worktrees)
git -C examples/06-adversarial-runaway/repo init -q && \
  git -C examples/06-adversarial-runaway/repo add -A && \
  git -C examples/06-adversarial-runaway/repo commit -qm "demo baseline"

markov-ci run examples/06-adversarial-runaway/config.yaml \
  --junit examples/06-adversarial-runaway/report.xml \
  --repo examples/06-adversarial-runaway/repo --seed 42
echo $?      # 1 = absorbed in a2_escalate_to_author
```

## Expected event stream

Seven events (`.markov-ci/events.jsonl`), every one carrying
`failure_category: type_mismatch`, `adapter: simulated`:

| Hop | Transition | What occurred |
|---|---|---|
| 1 | `s1_failure_triage → s2_agent_reasoning#1` | P(success) = **1.0** ≥ 0.40 → attempt 1 allowed |
| 2 | `s2_agent_reasoning#1 → s3_sandbox_validation#1` | patch proposed — sandbox rejects it |
| 3 | `s3_sandbox_validation#1 → s2_agent_reasoning#2` | loop back; P(success) = **1.0** → attempt 2 allowed |
| 4 | `s2_agent_reasoning#2 → s3_sandbox_validation#2` | patch rejected again |
| 5 | `s3_sandbox_validation#2 → s2_agent_reasoning#3` | loop back; P(success) = **1.0** → attempt 3 allowed |
| 6 | `s2_agent_reasoning#3 → s3_sandbox_validation#3` | third patch rejected |
| 7 | `s3_sandbox_validation#3 → a2_escalate_to_author` | **attempt cap: `max_attempts = 3` reached → escalate** |

The final hop is the *cap* gate, not the confidence gate: `attempt = 4 > max_attempts = 3`.

## What this proves

**Termination is a theorem, not a timeout.** Under `success = [1.0, 1.0, 1.0]` the loop
would run forever if left to the math — but `max_attempts` removes the final loop-back
edge at assembly time and renormalizes that mass into the designed absorbing states
(ADR-0004). So `I − Q` is invertible no matter what the priors say, and the run lands in
`a2_escalate_to_author` after exactly three attempts. Compare with a runtime step counter,
which treats the symptom *after* money burns: here the runaway loop is impossible by
construction, and `analyze` shows the user exactly where the run will stop.

## Forecast vs. actual

`markov-ci analyze --category type_mismatch` (on this config) predicts, from the
adversarial priors alone:

| Quantity | `analyze` forecast | this seeded run |
|---|---|---|
| P(absorbed in `a1`) | 0.924 | 0.0 (no patch satisfies the test) |
| P(absorbed in `a2`) | 0.076 | 1.0 (absorbed at the cap) |
| expected steps to absorption | 1.650 | 3 attempts made, then the cap stops |
| attempts before absorption | ≤ 3 (capped) | exactly 3, then `a2` |

The forecast's expected steps are small because the *optimistic prior* makes success
look likely — the demo's point is the opposite: **even when the forecast is wrong, the
cap still holds.** The worst case is bounded by `max_attempts`, whatever the priors
claim.
