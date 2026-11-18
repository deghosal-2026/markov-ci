# ADR-0009: Guardrails are enforced in code, never delegated

**Status:** Accepted
**Date:** 2026-11-16
**Amended by:** spec [0005 §1](../spec/0005-guardrails.md) — the allowlist now derives paths from the diff, and the always-denied set is broadened (`.env*` / `**/.env*`, `CODEOWNERS`, credentials/keys, CI + build configs, matched case-insensitively).

## Context

Safety instructions to an agent — "do not modify CI files", "do not weaken tests" —
are suggestions, not guardrails. Likewise, a harness's own allowlist or auto-accept
setting is not a control markov-ci owns. The most damaging observed anti-pattern is an
agent "fixing" a failing test by loosening the assertion: the build turns green and the
test suite's signal is destroyed.

Principles #3 (guardrails are code), #7 (governance is never delegated), and #8 (humans
merge) all point the same way.

## Decision

The following are implemented and enforced in the engine, applied to every patch
regardless of adapter:

1. **Write allowlist** (default `src/**`, `tests/**`) with an **always-denied set**
   (`.github/**`, `.git`, `*.env`, `**/secrets/**`, CI configs, lockfiles, `LICENSE`)
   that user configuration **cannot widen**.
2. **Test-modification-ratio hard stop** — `tmr > 1.0` or any assertion deletion
   escalates to `a2` and sets `mandatory_review`.
3. **Branch isolation** — patches only to `ai-fix/pr-<n>`; the PR branch and `main` are
   never touched.
4. **No force-push** — no such code path exists anywhere.
5. **No auto-merge** — `a1_ready_for_human_review` is terminal; merging is human work.

Harness/host settings are additive defense only; they never substitute for these.

## Considered options

- **Prompt instructions to the agent** ("do not touch CI files"). Rejected: a suggestion,
  not a control — the agent may ignore it.
- **Delegate to the harness's own allowlist / auto-accept settings.** Rejected: governance
  would then live outside markov-ci (principle #7) and vary per harness.
- **Enforce in the engine, applied to every patch (chosen).**

## Consequences

- Safety becomes **testable**: adversarial fixtures assert every rule.
- Some flexibility is deliberately removed — the always-denied set is not configurable,
  by design.
- TMR can produce false positives on legitimate test changes; the reviewer sees the
  ratio and the diff and can approve deliberately. Friction is placed where it belongs.
- The allowlist derives paths from the diff itself — both sides of renames/deletes, with
  git-quoted paths unescaped and post-apply verification by `git diff --name-status -M` —
  so a patch cannot smuggle a denied path past its declared set (spec 0005 §1).
- TMR stays **line-based**: it does not catch a meaning-preserving assertion rewrite
  (`assert f() == 2` → `assert True`). That is caught in human review, which is why `a1`
  is never auto-merged.
- **Falsifier:** any confirmed bypass of a guardrail is a security-class bug: add a
  regression test, fix the rule, and record it. The threshold is fixed at `1.0` in v0.1
  (spec 0005 §2 — there is no config key); making it tunable is a future decision, not a
  config change, and the hard stop is not tunable.
