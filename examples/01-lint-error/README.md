# Example 01 — lint error, first-pass fix

**Ships:** v0.1.0 · **Exit code to expect:** `0` · **Tutorial:** [01 — lint fix](../../docs/tutorials/01-lint-error-first-pass.md)

The happy path. A trivial lint failure is triaged, fixed by the simulated agent on
attempt 1, validated in the sandbox, regression-checked, and parked on an isolated
branch for human review — offline, deterministic, zero API keys.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the sandbox uses git worktrees)
git -C examples/01-lint-error/repo init -q && \
  git -C examples/01-lint-error/repo add -A && \
  git -C examples/01-lint-error/repo commit -qm "demo baseline"

markov-ci run examples/01-lint-error/config.yaml \
  --junit examples/01-lint-error/report.xml \
  --repo examples/01-lint-error/repo --seed 42
echo $?    # 0 = absorbed in a1 (ready for human review)
```

## Expected event stream

Four events, one per hop (`examples/01-lint-error/.markov-ci/events.jsonl`), every one
carrying `failure_category: lint_error`, `adapter: simulated`:

| Hop | Transition | What occurred |
|---|---|---|
| 1 | `s1_failure_triage → s2_agent_reasoning#1` | triage classified `lint_error`; log minimized to ≤ 200 lines |
| 2 | `s2_agent_reasoning#1 → s3_sandbox_validation#1` | agent patch passes the policy gates — prior P(success) = **0.92** ≥ 0.40 |
| 3 | `s3_sandbox_validation#1 → s4_regression_check` | patch applied in an isolated worktree; the failing test passes |
| 4 | `s4_regression_check → a1_ready_for_human_review` | regression suite clean → **absorbed** |

The patch sits on `ai-fix/local-<run_id>` — never your branch, never auto-merged
(spec 0005).

## What this proves

**The happy path is governed, not trusted.** Even when the first patch succeeds,
it does not reach your branch on the agent's word: it passes the path allowlist and
the test-modification-ratio check, is applied in a disposable git worktree, and only
then is the run parked in `a1_ready_for_human_review` for a person to merge. A green
agent is still a *proposal*. The event stream is the same evidence a reviewer sees.

## Forecast vs. actual

`markov-ci analyze --category lint_error` (before any run) predicts, from the shipped
priors alone:

| Quantity | `analyze` forecast | this seeded run |
|---|---|---|
| P(absorbed in `a1`) | 0.905 | 1.0 (attempt-1 patch) |
| expected steps to absorption | 1.591 | 1 (realized) |
| expected cost (cost_weight units) | 1.591 | 1.0 (realized) |

The forecast says *most* lint failures resolve on attempt 1; the seeded fixture
reproduces exactly that. Forecast and observed agree by construction — the simulated
agent is calibrated to the priors (ADR-0003).
