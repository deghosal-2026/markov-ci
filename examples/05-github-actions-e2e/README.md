# Example 05 — GitHub Actions, end-to-end

**Ships:** v0.2.0 (F15, F18) · **Exit code to expect:** `0` (absorbed `a1`) · **Tutorial:** [05 — GitHub Actions](../../docs/tutorials/05-github-actions-e2e.md)

The production wiring: the same governed loop, on a pull request, via the composite
Action at the repo root ([`action.yml`](../../action.yml)). It is the only demo that is
**live** — it runs on a GitHub runner against a real PR, not offline.

## The workflow

[`markov-ci.yml`](markov-ci.yml) is a copy-ready `.github/workflows/markov-ci.yml`. It
runs your fast checks to produce a JUnit report, then hands it to the Action:

```yaml
      - name: Govern the failure
        id: markov
        uses: deghosal-2026/markov-ci@v0.2.0
        with:
          config: .markov-ci/config.yaml
          junit: report.xml
          seed: 42
```

Full input/output contract: [how-to/integrate-github-actions](../../docs/how-to/integrate-github-actions.md).

## Expected output

The Action's step exposes the run outcome and uploads the evidence:

| Output | Happy path (`a1`) |
|---|---|
| `absorbing-state` | `a1_ready_for_human_review` |
| `exit-code` | `0` |
| `patch-branch` | `ai-fix/pr-<n>` |
| `run-id` / `events-path` | correlate with the uploaded `events.jsonl` artifact |

Exit code `0` = absorbed in `a1`. The patch sits on an isolated `ai-fix/pr-<n>` branch,
**never merged** — the Action posts the summary and stops; a human merges (principle 8).

## What this proves

**The governed loop is the same in CI as it is offline.** The Action is a thin wrapper
over the identical CLI: the same triage, policy gates, guardrails, and sandbox; the same
stable exit-code contract; the same versioned event stream. Nothing about running on a
runner loosens the rules — the Action **never merges** and **never force-pushes**, and
the workspace's own allowlists/budgets/caps apply regardless of the harness's settings
(principle 7). The one thing that is live is the *environment*: a real PR, a real
runner, and — for the opt-in harness rungs — real provider secrets, passed only to the
named harness adapter.

## Forecast vs. actual

`markov-ci analyze --category <category>` predicts the outcome before the PR runs; the
Action reports what actually happened.

| Quantity | Forecast (e.g. `unit_assertion`) | This PR run |
|---|---|---|
| P(absorbed in `a1`) | 0.885 | `a1` on the happy path |
| P(absorbed in `a2`) | 0.115 | `a2` when a guardrail/gate trips |
| expected attempts | 1.527 | 1 (seeded, offline agent) |

The forecast and the run agree because the default agent is calibrated to the priors
(ADR-0003). Point `adapter: harness` at a real harness and `recompute` the priors from
the uploaded event streams — the matrix then describes *your* agents, per category and
per harness (CUJ-4, CUJ-5).
