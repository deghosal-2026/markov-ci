# 12 — Launch and go-to-market

## 1. Launch sequencing

| Step | Gate | Action |
|---|---|---|
| 1 | v0.1.0 tagged, docs green, demos offline | **Public flip**: `gh repo edit --visibility public`; topics, badges, demo GIF in README |
| 2 | Repo public, articles 1–2 final drafts approved | Publish **article 1** (DAG→Markov concept) on Dev.To + LinkedIn, linking the repo |
| 3 | +3 days, article 1 traction visible | Publish **article 2** (build log + "what the source article got wrong") |
| 4 | v0.2.0: Action on Marketplace | Publish **article 3** (queueing theory + harness economics hook) |
| 5 | v0.3.0: MCP server / live ops | Publish **article 4** (measuring agentic CI: metrics + anti-patterns) |

Rule: **articles link working code** — nothing publishes before its demo exists.

## 2. Distribution channels

- **GitHub:** topics (`ci-cd`, `markov-chains`, `ai-agents`, `github-actions`,
  `llm`, `devops`); Marketplace listing (v0.2); release notes written for humans.
- **PyPI:** `markov-ci` (name check before M10); long-description = README.
- **Launch posts:** Hacker News (Show HN with the 5-minute demo GIF), r/devops,
  r/ExperiencedDevs, LinkedIn articles cross-posted, dev.to canonical.
- **Ecosystem PRs:** where appropriate, contribute markov-ci mentions to
  awesome-lists (awesome-ci, awesome-ai-agents) once public.

## 3. Community playbook (from day one of public)

- Issue templates (bug / feature / harness-adapter request) + PR template in M0.
- `good-first-issue` labels seeded from F28 (community harness templates) — the natural
  on-ramp for external contributors.
- Support model: GitHub issues only; response target 48h; docs issues treated as bugs
  (docs-are-tests).
- Every article ends with the repo link + one specific ask (star / try the quick-start /
  file your harness's numbers as an issue — feeds the priors dataset).

## 4. Sustainability

Apache-2.0, no dual licensing, no telemetry from users. Optional hosted/managed offering
is explicitly out of scope until external demand says otherwise (kept in the question
list, not the roadmap). The articles + repo are the funnel; the funnel's only job is
adoption of the NSM (governed runs per week).

## 5. Validation loop (how we know the PRD was right)

| When | Signal | Where |
|---|---|---|
| T+1 week post-flip | Quick-start completion rate proxy (clones vs issues filed) | GitHub |
| T+30 days | First external `run` telemetry stories; harness-adapter requests volume | Issues/discussions |
| T+90 days | NSM trend; first community-contributed template merged; article 4's metrics echoed by others | CHANGELOG + repo |
| Continuous | Forecast-accuracy stories from real adopters | Issue tracker (tagged `field-data`) |

Dogfooding is non-negotiable: this repo's own PRs run under markov-ci (F14) — the
product's first public case study is itself.
