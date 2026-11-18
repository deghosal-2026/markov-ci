# Release security & supply-chain gate — v0.1.1 (M15.4)

Re-run on the release commit (2026-11-18), against the project's own dependencies in
a **clean venv** (`pip install -e .`), mirroring the release workflow's `gate` job.

| Check | Command | Result | Log |
|---|---|---|---|
| History secret scan — trufflehog | `trufflehog git file://. --results=verified,unknown --no-update` | **0 verified, 0 unverified** — clean | `trufflehog.log` |
| History secret scan — gitleaks | `gitleaks detect --source . --no-banner --redact` | **140 commits, no leaks** | `gitleaks.log` |
| Dependency audit | `pip-audit` (clean venv) | **no known vulnerabilities** | `pip-audit.log` |
| SAST | `bandit -r src/markov_ci -ll` | **0 medium / 0 high** | `bandit.log` |
| License check | `pip-licenses --fail-on "GPL;AGPL"` | **pass** | `pip-licenses.log` |
| SBOM | `cyclonedx-py environment --of json` | **61 components**, CycloneDX 1.6 | `sbom.json` |

## Finding during this gate

`bandit` reported **B108** (`hardcoded_tmp_directory`) at `src/markov_ci/engine/container.py`:
the container's own `--tmpfs /tmp` mount (ADR-0012 §6), **not** a host temp dir. Suppressed
with a justified `# nosec B108` in the same commit; the gate is green.

## Attestations

PEP 740 build-provenance attestations are produced by the release workflow's Trusted
Publishing job (`actions/attest-build-provenance`, M13.34); they require the tagged
release run and are not reproducible locally.
