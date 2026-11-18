# Spec 0011 — Engine runtime

**Status:** Stable (v0.1 contract) · **Amends:** ADR-0012 (adds the container validation path) · **Implements:** PRD F8

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
    applied  = validation.apply_and_test(proposal)
    applied → s3#k: pass → s4 → (a1 | a2)
              fail → s2#(k+1) or a2
    emit transition event per hop (spec 0007) — append + flush
```

Single-threaded; no side effects outside the isolated patch branch.

## 2. Worktree validation (apply-and-test)

- Apply the patch in an isolated disposable validation copy — never the PR branch,
  never `main`. The copy is a **fresh clone** (`git clone --no-hardlinks --local`), so
  the host repo's hooks, config and credentials are not shared (ADR-0012 §1).
- Run only the failing tests first (fast signal), then full suite at `s4`.
- Revert on failure; the loop's next attempt starts from a clean tree.
- **Container path (v0.1.1, ADR-0012).** A container (`--network=none`, read-only
  checkout, tmpfs work dir, non-root) becomes the default for **fork PRs**; the clone
  remains the interim default elsewhere. Running the *examples* in Docker (#61) is
  packaging, not this path.
- **Not a full security boundary in v0.1.** The validation copy runs on the same kernel
  and filesystem as the host, but with an allowlisted environment (ADR-0012 §2), a
  process-group kill and resource limits (§3–§4); the container path is the real
  boundary (ADR-0012/ADR-0013, M13.18).

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
| `mandatory_review` | `true` when a hard stop (e.g. assertion deletion) needs a human |
| `events_path` | the JSONL evidence trail |
| `patch_branch` | the isolated branch, if any patch applied |
| `run_id` | correlates the result with the event stream (and the Action's run-id output) |

The human reviewer receives the full evidence; nothing agent-produced is silent.
