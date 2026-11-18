# 08 — Features: SHOULD / COULD / WON'T

## 1. SHOULD have (v0.2.0 — "capacity & reach")

**F15 — GitHub Action.** Root `action.yml` (composite) wrapping the CLI; Marketplace
listing; tested on a test repository's PRs.
**F16 — Queueing module.** Erlang-C (ρ, P_wait, Wq, p95 wait exact for M/M/c; λ ≥ cμ
rejected with guidance) + discrete-event simulator for bursty agent arrivals;
partitioning guidance for human vs agent pools.
**F17 — Monte-Carlo `simulate`.** Empirical absorption/cost stats; converges to analytic
B/C within CI.
**F18 — Demos 04–05.** `04-runner-pool-sizing` (Erlang-C + burst report);
`05-github-actions-e2e` (live PR workflow, opt-in secrets).
**F19 — Harness adapters (opt-in extras).** Real agents run through harness CLIs in
headless mode — `claude -p`, `opencode run`, `aider --yes-always` — plus a generic
bring-your-own-command adapter; markov-ci enforces its own allowlists/budgets regardless
of harness settings. Extras: `pip install markov-ci`; no network in this
repo's CI tests. Full strategy: [07-harness-compatibility.md](07-harness-compatibility.md).
**F20 — GitLab/Jenkins how-tos.** Same engine, adapter wiring documented.
**F21 — `recompute` pipeline.** events.jsonl → posterior matrix + CIs → config
round-trip; weekly-job recipe (cron + warehouse export).
**F22 — Property-based hardening.** hypothesis suite over matrix ops, triage parsing,
guardrail matching.

## 2. COULD have (v0.3+ — "live operations")

**F23 — Cost model in currency.** Per-state `$` cost vectors; org price cards.
**F24 — A/B policy comparison.** Two configs side-by-side: outcome/cost deltas.
**F25 — State-space visualization.** Mermaid graph + N-heatmap export from `analyze`.
**F26 — Multi-pipeline aggregation.** Org-level matrix across repos (warehouse-scale).
**F27 — Time-varying matrices.** Weekly automated recompute recipes; drift alerts when
empirical vs prior diverges beyond CI.
**F28 — Community harness adapters.** More verified headless-invocation templates
(Codex CLI, Goose, OpenHands, local-LLM runners) via the same protocol + T3 mechanism.
**F29 — MCP governance server.** Expose `analyze`/`validate`/`queue` as MCP tools so any
agent can query the governance model ("is another retry worth it?") before acting —
the CircleCI/Buildkite/Semaphore MCP-server pattern, applied to governance instead of
pipeline data. Requires F3, F16.

## 3. WON'T have (v0.x, deliberate)

Agent hosting/prompting (harnesses own that) · auto-merge (safety stance) ·
CI-system replacement (integration, not migration) · web dashboard (CLI + JSON only) ·
GUI matrix editor · guaranteed agent quality (we surface probabilities, we don't promise
outcomes) · speculative ML beyond Dirichlet posteriors.
