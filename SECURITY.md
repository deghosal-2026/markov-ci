# Security Policy

## Supported versions

markov-ci is **pre-alpha**. No released version is supported for production use yet.
Security fixes will be applied to the latest release once v0.1.0 ships.

## Reporting a vulnerability

**Do not open a public issue for security problems.** Until the repository is public,
report privately via GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on the repository (**Security → Report a vulnerability**).

Please include:

- affected version / commit,
- a minimal reproduction,
- the impact you believe it has,
- any suggested fix or mitigation.

**Response target:** acknowledgement within 72 hours; a fix or a documented workaround
for confirmed high-severity issues as fast as practicable for a single-maintainer
project. Credit is given in the release notes unless you ask otherwise.

## Security model (what markov-ci promises)

These are product guarantees, enforced in code and asserted by tests — treat a
violation as a security bug:

1. **Secrets never leave the run.** Telemetry events are validated against the schema
   and scrubbed; no secret material is ever emitted.
2. **No phoning home.** Telemetry is local, user-owned JSONL. markov-ci transmits
   nothing to any server.
3. **Least privilege by default.** Agent patches may write only to configured paths
   (`src/**`, `tests/**` by default); `.github/**`, secrets, CI configs, lockfiles, and
   `LICENSE` are **always denied** and cannot be enabled by configuration.
4. **Isolation.** Proposed patches are applied only in a disposable sandbox, never the
   PR branch, never `main`.
5. **No force-push, no auto-merge.** There is no code path that force-pushes or merges;
   the terminal state `a1_ready_for_human_review` requires a human.
6. **Bounded agent execution.** Token, wall-clock, and attempt caps make runaway
   execution structurally impossible.

## Supply chain

Runtime dependencies are pinned, minimal, and permissively licensed: `numpy`,
`pydantic≥2`, `PyYAML`, `typer`, `rich`, `jsonschema`. There are no post-install hooks.
The core package carries **no** LLM or agent-harness SDK dependency; harness adapters
live in the optional `markov-ci[harness]` extra.

### Release security gate (blocking)

No release is published — and the repository does not go public — until an automated,
**blocking** gate is green (tracked as issue #60):

- **Secret scan over the working tree *and full git history*** with `trufflehog`
  (verified findings) and `gitleaks`. History matters: a secret in an old commit is
  still a secret in every clone.
- **Dependency audit** with `pip-audit` against the shipped dependency set.
- **Static analysis** with `bandit` over `src/markov_ci` (no high-severity findings).
- **License check** — all runtime dependencies permissive.
- **SBOM** generated and attached to the release.
- **Trusted Publishing** — PyPI releases are published via OIDC with PEP 740
  attestations; no long-lived PyPI API token exists.

The gate is a required CI step on the release path; a release cannot publish while any
scanner reports an unresolved finding.

## See also

- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution workflow, quality bar, and the
  project principles contributors are held to.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community expectations.
