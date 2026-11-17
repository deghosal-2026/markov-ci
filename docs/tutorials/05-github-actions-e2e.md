# Tutorial 05 — GitHub Actions, end-to-end

**Demo:** `examples/05-github-actions-e2e` · **Ships:** v0.2.0 (F15, F18)
**Requires:** a real repo with PRs · opt-in secrets for live harness adapters

The production story: the same governed loop, wired into a pull-request workflow via
the composite Action — dogfooding setup, not a toy.

## 1. Add the workflow

`.github/workflows/markov-ci.yml` in your repo (full input/output contract in
[how-to/integrate-github-actions](../how-to/integrate-github-actions.md)):

```yaml
on:
  pull_request:
    branches: [main]

permissions:
  contents: write        # patch branch only — markov-ci never merges
  pull-requests: write   # posts the review summary

jobs:
  govern:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: deghosal-2026/markov-ci@v0.2.0
        with:
          config: .markov-ci/config.yaml
          junit: report.xml
          seed: 42
```

## 2. Let it run a PR

Push a PR with a trivially failing test. The workflow runs `s0` (your tests produce
`report.xml`), hands it to the Action, and markov-ci governs the rest:

- **Absorbed `a1`** → the Action posts a PR comment: patch branch link, expected vs
  observed cost, guardrail report, event-stream artifact. A human merges — or doesn't.
- **Absorbed `a2`/`a3`** → the comment carries the diagnostic context and the reason
  (decay gate, budget, hard stop).

## 3. Live agents (optional rung)

L3 of the adoption ladder: add `agent.adapter: harness` with your harness's headless
command (e.g. `claude -p --output-format json "%PROMPT%"`), store the provider key as a
repository secret, and mark the job's runner with your burst-pool label. Governance is
unchanged — allowlists, budgets, caps, and the no-auto-merge rule apply regardless of
harness settings (ADR-0007).

## 4. Close the loop

After a week of real PRs, export the run artifacts' `events.jsonl` and:

```bash
markov-ci recompute events.jsonl     # your org's empirical matrix, per category × adapter
```

Swap the recomputed priors into `config.yaml` — the matrix now describes *your* agents,
not the shipped defaults (CUJ-4, CUJ-5).

## What to notice

- This very repository runs the same setup on its own PRs (F14) — the first public
  case study is the project itself.
- Everything you saw offline in tutorials 01–03 is what the Action automates.
