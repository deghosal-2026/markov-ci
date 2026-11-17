# Spec 0005 — Guardrails

**Status:** Stable (v0.1 contract) · **Amends:** — · **Implements:** PRD F7

Guardrails are enforced in the engine, never delegated to the agent or its harness.

## 1. Path allowlist

- Config `agent.allow_write` (default: `src/**`, `tests/**`) — the only paths a patch
  may add/modify.
- **Always-denied regardless of config:** `.github/**`, `.git`, `*.env`,
  `**/secrets/**`, CI configs, lockfiles, `LICENSE`. A user cannot widen this set.
- Matching is against the post-patch file list; path traversal and symlink tricks must
  be blocked (adversarial fixtures are part of the test suite).

## 2. Test-modification-ratio (TMR) checker

- `tmr = test_lines_changed / src_lines_changed`.
- `tmr > 1.0` **or** any assertion deletion → hard stop to `a2` + `mandatory_review`
  flag on the RunResult.
- Rationale: an agent that "fixes" a failing test by weakening it has destroyed suite
  signal. This is anti-pattern #1 and is enforced, not merely documented.

## 3. Branch isolation

- Patches go to `ai-fix/pr-<n>` (or `ai-fix/local-<run_id>` for local runs).
- Never the PR branch; never `main`.
- **No force-push code path exists** — the branch manager has no force flag; a test
  asserts its absence.

## 4. No auto-merge

- Absorbing state `a1_ready_for_human_review` posts a review summary (diff link,
  telemetry, guardrail report) — and stops there. Merging is human-only.

## 5. RunResult evidence

Every run returns: absorbing state, per-state visit counts, tokens, wall-clock,
guardrail report, event-stream path. The human reviewer gets the full evidence trail —
nothing agent-produced is silent.
