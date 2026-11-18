# How-to: integrate with GitHub Actions

markov-ci ships a composite Action (root `action.yml`, F15, shipped in v0.1.0) that wraps the CLI.
This page is the input/output contract the Action must satisfy — the same contract
`tests/unit/test_action.py` asserts.

## Action contract

| Input | Required | Default | Meaning |
|---|---|---|---|
| `config` | no | packaged default | path to your markov-ci config YAML |
| `junit` | yes | — | JUnit XML produced by your test step |
| `repo` | no | `.` (the workspace) | repository to validate in isolation |
| `seed` | no | `42` | seeded determinism |
| `adapter` | no | `simulated` | `simulated` \| `harness` (opt-in extra) |
| `max-tokens` / `wall-clock` | no | from config | per-run budget overrides |

| Output | Meaning |
|---|---|
| `absorbing-state` | `a1` \| `a2` \| `a3` |
| `run-id` | correlates with the event-stream artifact |
| `patch-branch` | the isolated `ai-fix/pr-<n>` branch, if a patch applied |
| `events-path` | uploaded `events.jsonl` artifact |

## Minimal workflow

```yaml
name: markov-ci
on:
  pull_request:
    branches: [main]

permissions:
  contents: write        # patch branch only — the Action never merges
  pull-requests: write   # posts the review summary

jobs:
  verify-then-govern:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false     # the validation child must never see a token
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: s0 — fast checks
        run: pytest tests/unit --junitxml=report.xml || true
      - id: govern
        uses: deghosal-2026/markov-ci@v0.1.1
        with:
          config: .markov-ci/config.yaml
          junit: report.xml
          seed: 42
      - name: Escalate when the governed run needs a human
        if: always() && steps.govern.outputs.exit-code != '0'
        run: echo "absorbed in ${{ steps.govern.outputs.absorbing-state }}"
```

The step's exit code *is* the run outcome (`0/1/3/4/5`, spec 0008, ADR-0017) — branch on
it, or let `a2`/`a3` fail the job while the posted comment explains why. `@v0.1.1` is a
real released ref (do not pin to an unreleased version).

## Rules the Action enforces (non-negotiable)

1. **Never merges.** `a1` posts a summary and stops; merging is human work.
2. **Never force-pushes.** Patch branches are `ai-fix/pr-<n>`; concurrent runs for one
   PR append new branches rather than clobbering history.
3. **Least privilege by default.** `contents: write` is scoped by the branch manager to
   the patch branch; secrets are passed only to the named harness adapter, never to the
   simulated agent.
4. **Events are artifacts.** Every run uploads `events.jsonl` — your audit trail and
   your `recompute` input.

## See it live

`examples/05-github-actions-e2e` and
[tutorial 05](../tutorials/05-github-actions-e2e.md) walk the full PR lifecycle.
