# Security Policy

## Supported versions

markov-ci is **pre-1.0**. `v0.1.1` ("Trust") is the current release and the supported
line; `v0.1.0` is affected by the advisory below and should be upgraded.

| Version | Supported |
|---|---|
| `v0.1.1` | ✅ current — security fixes land here |
| `v0.1.0` | ❌ affected by GHSA-5jj3-gcw8-pm5g — upgrade to `>= 0.1.1` |

## Advisories

- **GHSA-5jj3-gcw8-pm5g (critical, `<= 0.1.0`).** The harness adapter ran
  `agent.harness.command_template` through a shell (`shell=True`) and substituted
  `%PROMPT%` into the command string with ad-hoc quoting, so any shell metacharacter in
  the prompt executed on the host. **Fixed in `0.1.1`** (ADR-0016): harness invocation is
  **argv-only** — the template is split with `shlex.split` before `%PROMPT%` is
  substituted, the prompt becomes one argv element, and the process runs with
  `shell=False`.

## Reporting a vulnerability

**Do not open a public issue for security problems.** Report privately via GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on the repository (**Security → Report a vulnerability**).

Please include the affected version/commit, a minimal reproduction, the impact you
believe it has, and any suggested fix. **Response target:** acknowledgement within 72
hours; a fix or documented workaround for confirmed high-severity issues as fast as
practicable for a single-maintainer project. Credit is given in the release notes unless
you ask otherwise.

## Security model

### Enforced today — asserted by tests; treat a violation as a security bug

1. **Secrets never leave the run.** Telemetry events are schema-validated and scrubbed;
   no secret material is emitted.
2. **No phoning home.** Telemetry is local, user-owned JSONL; markov-ci transmits nothing.
3. **Least privilege by default.** Patches may write only to configured paths (`src/**`,
   `tests/**` by default); `.github/**`, `.env*`, secrets, CI + build configs, lockfiles,
   `CODEOWNERS`, `LICENSE` and credentials/keys are **always denied** and cannot be enabled
   by configuration. Matching is case-insensitive (gitignore semantics).
4. **Guardrails derive paths from the diff.** The allowlist checks derived ∪ declared
   paths, fails closed when a non-empty diff's paths cannot be determined, denies symlink
   creation, and re-runs on git's own `git diff --name-status -M` after apply.
5. **Patches only to throwaway copies.** Validation runs in a **fresh clone**
   (`git clone --no-hardlinks --local`) — the host repo's hooks, config and credentials
   are not shared — and never the PR branch or `main`.
6. **Scrubbed child environment.** The validation child gets only `PATH`, `LANG` and a
   temp `HOME` (plus config-listed vars); `GITHUB_TOKEN`, `ACTIONS_*` and
   `*_TOKEN`/`*_KEY`/`*_SECRET` are dropped.
7. **Bounded execution.** Attempt caps make the **model** acyclic after the cap; at
   runtime a hung child is killed on timeout **with its whole process group**, under
   `resource` limits (CPU / address space / file size), and every call gets
   `min(configured_timeout, remaining_wall_clock)`; a timeout absorbs in `a3` with an event.
8. **Opt-in container isolation.** `--container-image` (or `container:` in config) runs
   validation in a container: `--network=none`, read-only checkout, tmpfs work dir,
   non-root. Recommended (and the Action default) for fork PRs.
9. **No force-push, no auto-merge.** No code path force-pushes or merges; the terminal
   state `a1_ready_for_human_review` requires a human.

### Known limitations — do not over-rely on these

- **Token caps** bind only for adapters that **report usage**; unknown usage is recorded
  as `null`, so the cap is not a hard guarantee for every adapter (spec 0007).
- **Pinned dependencies.** Runtime dependencies are **lower-bounded**, not hash-pinned
  (see Supply chain).
- **Container isolation is opt-in.** Without it, validation shares the host kernel and
  filesystem (a clone, scrubbed env and limits — not a kernel boundary). ADR-0012.

## Supply chain

Runtime dependencies are **lower-bounded** (not hash-pinned), minimal, and permissively
licensed: `numpy`, `pydantic≥2`, `PyYAML`, `typer`, `rich`, `jsonschema`, `defusedxml`
(hardened JUnit parsing), `pathspec` (gitignore semantics). There are no post-install
hooks. The core carries **no** LLM or agent-harness SDK dependency; the harness adapters
are stdlib-only and live in the core.

### Release security gate (blocking)

No release is published until an automated, **blocking** gate is green:

- **Full test suite** on Python 3.11–3.13, `ruff`, `mypy --strict`, and **branch coverage
  ≥ 95%**.
- **Secret scan over the working tree *and full git history*** with `trufflehog`
  (verified findings) and `gitleaks`.
- **Dependency audit** with `pip-audit` against the shipped dependency set.
- **Static analysis** with `bandit` over `src/markov_ci` (no medium/high findings).
- **License check** — all runtime dependencies permissive.
- **SBOM** generated and attached to the release.
- **Every action pinned by full commit SHA** (Dependabot keeps them fresh).
- **PyPI publishing via Trusted Publishing** (OIDC + PEP 740 `attest-build-provenance`)
  in a protected `environment: pypi` — no long-lived token (M13.34).

The gate is a required CI step on the release path; a release cannot publish while any
scanner reports an unresolved finding. The v0.1.1 re-run is recorded in
`field-test/v0.1.1/security/`.

## See also

- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution workflow, quality bar, and the
  project principles contributors are held to.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community expectations.
