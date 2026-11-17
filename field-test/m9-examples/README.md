# Field test — M9 offline proof suite + Docker runner (2026-11-16)

Raw logs of the M9 validation runs, preserved exactly as produced (byte-verified
copies). **This directory is hand-maintained evidence — no automation writes
here; nothing in this tree may be overwritten or regenerated.**

Environment: macOS (host) · Docker Compose · image `python:3.12-slim` + git
(Python 3.12.16, git 2.47.3, pytest 9.2.0 inside the container).

## Run order and what each file is

| File | Run | Verdict |
|---|---|---|
| `m9-gate.log` | `make gate` on commit `0f5f327` (ruff + `mypy --strict` + full suite + coverage) | clean · clean · **458 passed** · **96.73%** (≥95% required) |
| `m9-docs.log` | `make docs` (mkdocs `--strict`) on `0f5f327` | built in 0.34s |
| `m9-docker.log` | **First** container exercise of the M9.6 Docker runner (image built from `0f5f327`) | build OK · demo-03 exit **2** ✓ · demo-04 exit **0** ✓ · **demo-01 exit 1 ✗ · demo-02 exit 1 ✗ — found issue:** the image lacked `pytest`, so the sandbox died on `FileNotFoundError: 'pytest'` (the `run` CLI's default failing command is `pytest -q`) |
| `m9-docker2.log` | Rebuild with the pytest fix in the working tree | interrupted mid-build (partial log, kept for the record) |
| `m9-deep-validate.sh` | The deep-validation script: build + compose acceptance + image env + per-demo evidence checks | — |
| `m9-deep-validate.log` | Deep validation run against the fixed image (working tree = the Dockerfile later committed as `8de54f0`) | build exit 0 · **demo-01 → 0, demo-02 → 2, demo-03 → 2, demo-04 → 0** (all under `network_mode: none`) · image env checks pass (`pip check` clean) · demo-02: `a2`, 5 events, `s2#3` never reached · demo-03: exit 2 at triage, no events dir · demo-04: Erlang-C p95 13.27 min vs DES 12.92 min · `tests/unit/test_docker.py` 4 passed. Note: the demo-01 deep block in this log died on a **caller quoting bug** in the script (single-quoted f-string closed the `sh -c` block); the real demo-01 evidence is the re-run below |
| `m9-deep-demo01.sh` + `m9-deep-demo01.log` | Demo-01 deep check, re-run with fixed quoting | exit 0 · `a1_ready_for_human_review` · 4 events, all `lint_error` / `adapter: simulated`, hops `s1 → s2#1 → s3#1 → s4 → a1` · repo untouched after the run (`git status --porcelain` empty) · **two seeded runs → IDENTICAL** (absorbing / visits / tokens) |

## Verdict for the milestone

- M9 offline demos (01–04) reproduce **in the container, offline**, with the
  documented exit codes and byte-stable results under `--seed`.
- The found issue (missing `pytest` in the image) was fixed in `8de54f0` and
  re-validated from scratch; see the #61 close comment for the summary table.
- `05-github-actions-e2e` (#45) was **not** run: it requires M10.1 (root
  `action.yml`) and a live PR — tracked open on the issue.
