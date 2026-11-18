# ADR-0013: Trust boundary — untrusted input never crosses into the host

**Status:** Accepted
**Date:** 2026-11-17

## Context

The v0.1.1 review (FIX-04 §7) found the trust boundaries were never written down, so
each control was argued case by case. The engine executes code and agents that respond
to attacker-influenced input: a fork PR's diff, its test output, harness output, and
repo rule files read from the untrusted tree. Without a stated boundary there is no
answer to "is this safe?" that does not depend on the reviewer's memory.

## Decision

We draw one boundary and state who crosses it.

**Untrusted inputs** (attacker-influenceable, never trusted):

- PR code and the applied patch.
- Test command output, and JUnit/telemetry parsed from it.
- Harness / agent output.
- Repo rule files (config, templates) read from the PR tree.

**Assets** (must never be reachable from untrusted execution):

- `GITHUB_TOKEN` and any CI token.
- Provider keys (`*_TOKEN` / `*_KEY` / `*_SECRET`).
- The repo, its branches, and its git state.

**Policy:**

- **Fork PRs run the hardened path.** Container isolation (ADR-0012) is the default; the
  harness adapter is **not** run for untrusted authors until that default lands — an
  interim safety notice states this (M12.7).
- **`pull_request_target` is prohibited** in shipped workflows: it hands a fork PR the
  base repo's secrets.
- **Token handling:** least scope; `persist-credentials: false` on every checkout; the
  validation child never inherits a token (ADR-0012).
- **Guardrails run before any agent** (ADR-0008) and are enforced in code (ADR-0009) on
  the paths **derived from the diff**, never on declared ones.

## Considered options

- **Trust the PR author; rely on the harness's own allowlist.** Rejected (ADR-0009):
  governance is never delegated.
- **Run validation on the host and rely on review.** Rejected: review does not remove a
  credential from the child's environment.
- **Explicit threat model with a fork-PR container default.** Chosen.

## Consequences

- Every control has a stated threat, so "is this safe?" is answerable against this
  boundary rather than against a reviewer's memory.
- Untrusted PRs from forks get the strongest path from day one; other runs follow.
- **Falsifier:** any demonstrated crossing of untrusted input into an asset is a
  security-class bug — fix the boundary, add a regression test, record it.
