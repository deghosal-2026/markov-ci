# Spec 0011 — Engine runtime

**Status:** Stable (v0.1 contract) · **Implements:** PRD F8

## 1. The governed loop

```
run(config, junit, logs, adapter) -> RunResult:
  triage → category (spec 0010)
  assemble augmented matrix for (category, adapter) (spec 0002)
  state ← s1 → (s2#1 | a2)
  loop:
    policy gates in strict order (spec 0004):
      budget trip      → a3   (record event, stop)
      attempt cap      → a2   (record event, stop)
      low confidence   → a2   (record event, stop)
    proposal = adapter.repair(ctx)            (spec 0006)
    report   = guardrails.check(proposal)     (spec 0005)  — deny → a2
    applied  = sandbox.apply_and_test(proposal)
    applied → s3#k: pass → s4 → (a1 | a2)
              fail → s2#(k+1) or a2
    emit transition event per hop (spec 0007) — append + flush
```

Single-threaded; no side effects outside the isolated patch branch.

## 2. Sandbox apply-and-test

- Apply the patch in an isolated git worktree — never the PR branch, never `main`.
- Run only the failing tests first (fast signal), then full suite at `s4`.
- Revert on failure; the loop's next attempt starts from a clean tree.

## 3. Crash-safety

- Every hop appends one JSONL event and flushes before proceeding.
- A killed run leaves a valid partial event stream; the absorbing state is simply
  absent, which is itself auditable.

## 4. RunResult

| Field | Content |
|---|---|
| `absorbing_state` | `a1` \| `a2` \| `a3` |
| `visits` | per-state visit counts |
| `tokens_used`, `wall_clock_ms` | totals |
| `guardrail_report` | allowlist/TMR decisions + flags |
| `events_path` | the JSONL evidence trail |
| `patch_branch` | the isolated branch, if any patch applied |

The human reviewer receives the full evidence; nothing agent-produced is silent.
