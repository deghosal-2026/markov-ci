# Tutorial 01 — Lint error, first-pass fix

**Demo:** `examples/01-lint-error` · **Ships:** v0.1.0 · **Exit code to expect:** `0`

The happy path: a trivial lint failure is classified, fixed by the (simulated) agent on
attempt 1, validated in the worktree validation, regression-checked, and parked on an isolated
branch for human review — all offline, all deterministic.

## Run it

```bash
# one-time: the demo repo must be a real git repository (the validation copy uses git worktrees)
git -C examples/01-lint-error/repo init -q && \
  git -C examples/01-lint-error/repo add -A && \
  git -C examples/01-lint-error/repo commit -qm "demo baseline"

markov-ci run examples/01-lint-error/config.yaml \
  --junit examples/01-lint-error/report.xml \
  --repo examples/01-lint-error/repo --seed 42
echo $?
```

## What happens, hop by hop

| Hop | State | What occurred |
|---|---|---|
| 1 | `s1 → s2#1` | triage classifies `lint_error`; log minimized to ≤ 200 lines |
| 2 | `s2#1 → s3#1` | agent patch passes the policy gates — prior P(success) = **0.92** ≥ 0.40, attempt 1 of 3 |
| 3 | `s3#1 → s4` | patch applied in isolated worktree; failing test passes |
| 4 | `s4 → a1` | regression suite clean → **absorbed: ready for human review** |

Exit code `0` = absorbed in `a1`. The patch sits on `ai-fix/local-<run_id>` — never
your branch, never auto-merged (spec 0005).

## Read the evidence

```bash
cat examples/01-lint-error/.markov-ci/events.jsonl
```

Four events, one per hop — each carries `failure_category: lint_error`,
`attempt`, and `adapter: simulated` (see [telemetry reference](../reference/telemetry.md)).
The run's `RunResult` (absorbing state, visit counts, tokens, guardrail report) is the
same evidence a human reviewer sees on the PR.

## The math behind what you just watched

`lint_error` priors are `success: [0.92, 0.65, 0.20]` (spec 0001 §4) — so the forecast
says most lint failures resolve on attempt 1, which is exactly what the seeded fixture
reproduces. Forecast (`analyze --category lint_error`) and observed run agree by
construction: the simulated agent is calibrated to the priors (ADR-0003).

## What to notice

- No API key was used — `SimulatedAgent` is the default adapter.
- Same `--seed` → byte-identical run; CI asserts this.
- Had the patch touched anything outside `src/**` / `tests/**`, the guardrails would
  have hard-stopped to `a2` instead.
