# Field test — M14 (v0.1.1)

Raw, committed evidence that the **M13 fixes hold outside the unit suite**. Mirrors the
`field-test/m9-examples` and `field-test/m10-action-e2e` layout.

> **This directory is hand-maintained evidence.** The report
> (`FIELD_TEST_REPORT.md`) is written by hand and **no automation may overwrite,
> regenerate, or clobber it** — the runner writes only its own `*.log` / `*.txt`
> outputs. Nothing here may be rewritten by a script.

**Environment:** macOS arm64 (Darwin 25.6.0) · Python 3.14.5 · Docker 29.9.2 ·
git `0779334` · markov-ci `0.1.0` (unchanged in v0.1.1) · run 2026-11-18 04:46 UTC.

## How to reproduce

```sh
python3 field-test/v0.1.1/run-field-test.py          # demos, injection, guardrail, budget/isolation
docker compose build && for d in demo-01 demo-02 demo-03 demo-04; do docker compose run --rm "$d"; done
```

## Files

| File | Case | Produced by |
|---|---|---|
| `env.txt` | M14.1 environment (date, uname, python, commit, docker) | runner |
| `demos.log` | M14.2 demos 01–07: exit codes, event streams, `--seed` stability | runner |
| `docker.log` | M14.2 Docker runner: build + `docker compose run` demos under `network_mode: none` | `docker compose` |
| `injection.log` | M14.3 FIX-01 payloads against the real runner | runner |
| `guardrail.log` | M14.4 FIX-02 adversarial diffs through a real git repo | runner |
| `budget-isolation.log` | M14.6 timeout → a3, scrubbed env, process-group kill | runner |
| `results.txt` | the runner's machine summary (23 cases) | runner |
| `run.log` | the full runner stdout for this run | runner |
| `FIELD_TEST_REPORT.md` | per-case P/F, found issues, verdict — **hand-maintained** | human |

## Cases and verdicts

23/23 runner cases **PASS**; 4/4 Docker demos **OK** under `--network none`
(`docker.log`). Two real issues were found and fixed (see the report):

- **F-1** — `run` mapped a compile-time config error (no prior for the failure
  category) to an unhandled traceback / exit 1 instead of exit 4 (invalid config).
- **F-2** — `compose.yaml` demo exit codes were stale after the `a2: 2 → 1` change
  (demo-02/03 expected `2`).

`M14.5` (live Action against a real PR) is **blocked** — it needs an authenticated
PR run and opt-in secrets that cannot be produced in this environment.
