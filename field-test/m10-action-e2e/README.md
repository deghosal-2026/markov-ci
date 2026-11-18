# Field test — the composite Action on a live GitHub runner (2026-11-16)

Live end-to-end runs of the root composite Action (`action.yml`), exercising M10.1 (#46)
and M9.5 (#45). **Hand-maintained evidence — no automation writes here.**

Logs are preserved verbatim; the absolute paths in them are the GitHub-hosted runner's
(`/home/runner/...`), not a maintainer's.

Workflow: `.github/workflows/markov-ci-e2e.yml` (workflow_dispatch) · Action: `uses: ./`
· target: the bundled `examples/01-lint-error` demo · runner: GitHub-hosted
`ubuntu-latest`, Python 3.12.

| File | Run | Outcome |
|---|---|---|
| `run-44001036549-failed.log` | first attempt (@ `4ca2293`) | **FAILED** — found a real wiring bug: the action ran `bash "${{ github.action_path }}/run.sh"`, but the script lives at `action/run.sh`, so the step died with `No such file or directory` (exit 127). Offline tests invoke `action/run.sh` directly and cannot exercise `github.action_path`. |
| `run-44001110296-success.log` | after the fix (@ `8078ec9`) | **SUCCESS** — the Action installed markov-ci, governed the failure, and the asserting step read back the documented outputs |
| `run-success-meta.txt` | the successful run's metadata | `sha=8078ec9…`, `conclusion=success`, run URL |

## Successful run — the Action's outputs on the runner

```
absorbing-state=a1_ready_for_human_review
exit-code=0
run-id=68376f0d400b4c3fb6ab81f5cd790c98
patch-branch=ai-fix/local-68376f0d
```

The `Assert the governed outcome` step tested both and passed, so the job concluded
success. That is the full contract: the Action wraps the CLI, the run absorbs in `a1`,
nothing is merged, and the outputs/exit-code are what the docs promise.

## Verdict

- **M10.1 (#46)** — the composite Action is built and now verified on a real GitHub
  runner (contract + offline run of `action/run.sh` + the live e2e above).
- **M9.5 (#45)** — the workflow runs on a real runner against a real checkout and
  produces the documented outcome; the live run is no longer outstanding.
