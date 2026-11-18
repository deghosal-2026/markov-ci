# 09 — CLI/UX, documentation, quality, security & privacy

## 1. CLI surface (F10)

| Command | Purpose | MUST/SHOULD |
|---|---|---|
| `markov-ci validate [config]` | Validate + summarize assembled matrix | MUST |
| `markov-ci analyze [config] [--category C] [--json]` | N, B, t, C + CIs | MUST |
| `markov-ci run [config] --junit X [--seed S]` | Governed remediation loop | MUST |
| `markov-ci queue --lambda L --mu M --c N [--simulate]` | Runner-pool math | SHOULD |
| `markov-ci simulate [config] --runs N` | Monte-Carlo absorption/cost | SHOULD |
| `markov-ci recompute <events.jsonl>` | Empirical matrix from telemetry | SHOULD |

**Exit-code contract (stable API):** 0 = `a1` · 2 = `a2` · 3 = `a3` · 4 = invalid
config/input. CI branches on it.

**UX principles:** (1) zero-config first run works; (2) exit codes are a contract;
(3) human output via `rich`, machine output via `--json` — same information, never
prose-parsing; (4) every printed number traces to config + telemetry — no magic
constants; (5) adapter selection is explicit (`agent.adapter`), and the active adapter
appears in every run header and event.

## 2. Documentation requirements (F12)

In-repo (MUST): OVERVIEW, this PRD folder, [spec/](../spec/README.md) contracts, WBS,
quick-start (5 min, no API key), architecture, math derivation
(explanations/markov-model.md), queueing explanation, design-review ("what the source
article got wrong"), config/telemetry/CLI reference, tutorials per demo, 7 ADRs,
CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CHANGELOG. mkdocs site builds in CI;
**docs-are-tests**: quick-start commands execute verbatim in CI.

Published (O6): four articles — (1) DAG→Markov concept; (2) build log incl. corrections
to the source article; (3) queueing theory for runner fleets, incl. harness economics
(the ~70× token-variance study is the hook); (4) measuring agentic CI. Each links a
runnable demo; publishing gated on the public flip (see [12-launch-and-gtm.md](12-launch-and-gtm.md)).

## 3. Quality attributes

| Attribute | Requirement |
|---|---|
| Correctness | Math property-tested; golden fixtures; forecast-vs-simulation within CI |
| Determinism | Seeded RNG everywhere; demos byte-stable |
| Performance | [03](03-goals-and-metrics.md) §4 targets |
| Security | See §4 below |
| Compatibility | Python 3.11–3.13; no runtime LLM/harness SDK in core |
| Maintainability | `mypy --strict` + `ruff` clean; one owner per module (schema, guardrails, math) |
| Concept accessibility | Every doc readable without prior Markov knowledge; math isolated to explanations/ |

## 4. Security requirements (binding)

1. **Secrets never in events/logs/output** — schema-enforced + scrub test.
2. **Worktree isolation** — patches apply in a disposable worktree, never the PR branch.
3. **Least privilege at the adapter seam** — harness subprocesses inherit no CI secrets
   beyond what triage minimized; token scopes documented per integration template.
4. **Supply chain** — pinned, minimal runtime deps; no post-install hooks; extras
   pull nothing beyond their named harness wrapper.
5. **Patch provenance** — every patch is attributable to (run_id, adapter, attempt)
   in the event stream; the guardrail report travels with the RunResult.
6. **Release security gate (blocking).** No release is published and the repo does not
   flip public until a blocking gate passes: secret scan over the working tree **and
   full git history** (`trufflehog` + `gitleaks`), dependency audit (`pip-audit`),
   static analysis (`bandit`), runtime-dependency license check, and an SBOM attached
   to the release. Publishing uses PyPI **Trusted Publishing** (OIDC) with PEP 740
   attestations — no long-lived API token. Tracked as M10.8 (#60).

## 5. Privacy requirements

**markov-ci phones home to no one.** Telemetry is local JSONL, user-owned, user-shipped
(the opposite of most CI tools). Events contain commit SHAs and PR numbers —
organizations choose where they flow (warehouse recipes are docs, not defaults). This
is a trust feature and gets stated in the README.
