# Spec 0005 — Guardrails

**Status:** Stable (v0.1 contract) · **Amends:** ADR-0009 (§1 derives paths from the diff and broadens the always-denied set) · **Implements:** PRD F7

Guardrails are enforced in the engine, never delegated to the agent or its harness.

## 1. Path allowlist

- Config `agent.allow_write` (default: `src/**`, `tests/**`) — the only paths a patch
  may add/modify.
- **Paths are derived from the diff, not declared.** The engine parses `diff --git`,
  `---`/`+++`, `rename from/to`, `copy from/to`, collecting **both** old and new paths;
  text after a tab is dropped, `/dev/null` is skipped, the first path component is
  stripped (`-p1`), and git C-style quoted paths (`\\`, `\"`, `\t`, `\n`, octal `\NNN`)
  are unescaped before matching.
- The check is against **derived ∪ declared** paths. A non-empty diff with no derivable
  paths **denies** (`could not determine the paths this patch touches`); a symlink
  creation (`mode 120000`) denies and is recorded in the guardrail report. The diff
  **fails closed**.
- **Post-apply verification:** after `git apply` and before the test command, the
  allowlist is re-run on `git diff --name-status -M` in the worktree, so git is the
  source of truth for what actually changed.
- **Always-denied regardless of config:** `.github/**`, `.git`, `.env*` / `**/.env*`,
  `**/secrets/**`, CI + build configs for common systems, `CODEOWNERS`,
  credentials/keys, lockfiles, `LICENSE`. Matching is **case-insensitive** (gitignore
  semantics, via `pathspec`). A user cannot widen this set.
- Path traversal and symlink tricks are blocked; adversarial fixtures (delete/rename a
  CI config, quoted escaped paths such as `\056github`) are part of the test suite.

## 2. Test-modification-ratio (TMR) checker

- `tmr = test_lines_changed / src_lines_changed`.
- `tmr > 1.0` **or** any assertion deletion → hard stop to `a2` + `mandatory_review`
  flag on the RunResult.
- A deleted file is classified by its **original** path; a deleted test file counts as
  test lines.
- Rationale: an agent that "fixes" a failing test by weakening it has destroyed suite
  signal. This is anti-pattern #1 and is enforced, not merely documented.
- **Known limitation:** TMR is line-based, so a rewrite that keeps a line's shape but
  removes its meaning — `assert f() == 2` → `assert True` — is **not** caught by the
  ratio. It is caught by human review of the diff, which is why `a1` is always a human
  decision (ADR-0009); the ratio is a tripwire, not a proof.

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
