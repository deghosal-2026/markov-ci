# ADR-0012: Execution isolation — validation runs in a disposable, resource-bounded copy

**Status:** Accepted
**Date:** 2026-11-17

## Context

The v0.1.1 review (FIX-04 §1) found that markov-ci called its validation step a
"sandbox" while it provided no isolation: the patch was applied in a `git worktree`
that shares the host repo's hooks, config and credentials; the child process inherited
the environment (including `GITHUB_TOKEN` and `ACTIONS_*`); a timeout killed only the
direct child, not its descendants; there were no CPU / address-space / file-size limits;
and captured output was unbounded. A hostile or runaway patch therefore ran with the
host's authority, and the product claim "sandbox" overstated what the code did.

Deterministic triage, guardrails and budgets are decisions we already own (ADR-0008,
ADR-0009). This ADR decides the *execution boundary* those controls apply inside.

## Decision

Validation **never runs in the host checkout**; it runs in a **disposable validation
copy**:

1. **Fresh clone, not a shared worktree** — clone into a temp dir
   (`git clone --no-hardlinks --local`) so hooks, config and credentials are not shared
   with the host; clean up via a context manager.
2. **Allowlisted environment** — pass only `PATH`, `HOME`→temp, `LANG` and
   config-listed vars; drop `GITHUB_TOKEN`, `ACTIONS_*`, `*_TOKEN` / `*_KEY` /
   `*_SECRET`.
3. **Whole-tree kill** — `start_new_session=True` + `os.killpg` on timeout (Job Object
   on Windows); capture at most the last 1 MB of output.
4. **Resource limits** — `resource.setrlimit` (CPU, address space, file size) in
   `preexec_fn` on POSIX.
5. **Remaining-wall-clock budget** — every harness and validation call receives
   `min(configured_timeout, remaining_wall_clock)`; a timeout absorbs in `a3` **with an
   event**.
6. **Container isolation** — `--network=none`, read-only checkout, tmpfs work dir,
   non-root — is the option that makes isolation real, and is the **default in the
   Action for fork PRs**.

The word **"sandbox" is retired** in favour of **"worktree validation"** until the
container path is the default everywhere; user-facing text must not promise isolation
the code does not provide.

## Considered options

- **Status quo — shared `git worktree`, inherited environment.** Rejected: shares host
  hooks and credentials, so a hostile patch runs with host authority.
- **Worktree + environment scrub + budgets, no container.** Cheaper and OS-portable, but
  still shares a kernel and filesystem; protects credentials and the host repo, not the
  machine. Chosen as the **interim** default, with the untrusted-PR safety notice
  (M12.7).
- **Container as the default everywhere.** The strongest boundary; adopted as the
  **fork-PR default** now, with wider rollout as the follow-up.

## Consequences

- Credentials, hooks and the host repo are out of reach of the validation child — a
  checkable, testable claim.
- "sandbox" disappears from the vocabulary; "worktree validation" is honest about the
  interim boundary.
- We pay for it: a clone per run, and a container dependency for fork PRs. That is the
  price of a real boundary.
- **Falsifier:** any path by which the validation child reaches a host credential, the
  host repo, or an unbounded resource is a security-class bug — fix the boundary, add a
  regression test, record it.
