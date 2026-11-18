# Field-test report — M14 (v0.1.1)

> **Hand-maintained. Do not overwrite.** This report is written and edited by hand;
> no script, generator, or automation may regenerate, replace, or clobber it. The
> runner (`run-field-test.py`) writes only the `*.log` / `*.txt` evidence files next
> to it. Keep every note and verdict here; if a case changes, edit this file by hand.

- **Milestone:** M14 — Field test (v0.1.1)
- **Run:** 2026-11-18 04:46 UTC
- **Environment:** macOS arm64 (Darwin 25.6.0) · Python 3.14.5 · Docker 29.9.2
- **Commit:** `0779334` · **Version:** markov-ci `0.1.0` (unchanged in v0.1.1)
- **Evidence:** `env.txt`, `demos.log`, `docker.log`, `injection.log`,
  `guardrail.log`, `budget-isolation.log`, `results.txt`, `run.log`

## Summary

| Case | What it proves | Result |
|---|---|---|
| M14.1 | field-test dir + runner + environment captured | **PASS** |
| M14.2 | demos 01–07 reproduce their documented exit codes, event streams, `--seed` byte-stability | **PASS** (7/7) |
| M14.2 (Docker) | demos 01–04 run under `--network none` with documented exit codes | **PASS** (4/4) |
| M14.3 | FIX-01 injection payloads are inert through the real runner | **PASS** (9/9) |
| M14.4 | FIX-02 adversarial diffs end `a2` with a guardrail report; the sandbox is never invoked | **PASS** (3/3) |
| M14.5 | live composite Action against a real PR | **BLOCKED** |
| M14.6 | remaining-timeout → `a3` with an event; scrubbed env hides `GITHUB_TOKEN`; process-group kill | **PASS** (3/3) |
| M14.7 | this report | **PASS** |
| M14.8 | failures filed; release readiness not blocked | **PASS** (see F-1/F-2) |

## M14.2 — offline demos 01–07 (`demos.log`)

| Demo | Command | Documented exit | Observed | Verdict |
|---|---|---|---|---|
| 01-lint-error | `run … --seed 42` | 0 | 0 | **PASS** |
| 02-unit-assertion-decay | `run … --seed 42` | 1 | 1 | **PASS** |
| 03-infra-timeout | `run …` | 1 | 1 | **PASS** |
| 04-runner-pool-sizing | `queue … --simulate --json` | 0 | 0 | **PASS** |
| 05-github-actions-e2e | (workflow demo — no CLI command) | — | — | n/a |
| 06-adversarial-runaway | `run … --seed 42` | 1 | 1 | **PASS** |
| 07-cheating-agent | `run … --seed 42` | 1 | 1 | **PASS** |

`--seed` byte-stability: two seeded runs produced identical `visits` for 01, 02, 06
and 07 (`demos.log`). Event streams match the READMEs hop-for-hop (also asserted in
the suite by `tests/e2e/test_examples.py::test_cli_example_event_stream_matches_its_readme`).

### Docker runner (`docker.log`) — `network_mode: none`

| Demo | Documented exit | Observed | Verdict |
|---|---|---|---|
| demo-01 | 0 | 0 | **OK** |
| demo-02 | 1 | 1 | **OK** |
| demo-03 | 1 | 1 | **OK** |
| demo-04 | 0 | 0 | **OK** |

The first Docker pass **failed** on demo-02/03 (`FAIL: expected exit 2, got 1`) — see
**F-2**; the fixed run is the "after" block in `docker.log`.

## M14.3 — injection field test (`injection.log`)

Nine FIX-01 payloads (`$(…)`, backticks, the `"` breakout, `;`, `|`, `&&`, newline,
`$HOME`, `>`) were carried in a JUnit failure message and run through the **real**
`markov-ci run` with `adapter: harness` (an echo child). **No marker file was
created for any payload** (9/9) — nothing re-parsed the prompt.

## M14.4 — guardrail field test (`guardrail.log`)

Each adversarial diff was emitted by a harness against a real git repo:

| Case | Guardrail report | Sandbox invoked | Exit | Verdict |
|---|---|---|---|---|
| delete-ci | `.github/workflows/ci.yml: always-denied (.github)` | no | 1 (`a2`) | **PASS** |
| rename-into-github | `notes.md: not in the allowlist` + `.github/workflows/evil.yml: always-denied (.github)` | no | 1 (`a2`) | **PASS** |
| quoted-octal | `.github/workflows/ci.yml: always-denied (.github)` | no | 1 (`a2`) | **PASS** |

Both sides of the rename are reported; the `\056github` C-quoted path is unescaped and
caught; the `s3_sandbox_validation` hop is **never** reached.

## M14.6 — budget & isolation (`budget-isolation.log`)

| Check | Result |
|---|---|
| remaining-timeout | exit **3**, last event `→ a3_budget_exceeded` — **PASS** |
| scrubbed env | child saw only `HOME`, `LANG`, `PATH` (+ `__CF_USER_TEXT_ENCODING`); `GITHUB_TOKEN` **absent** — **PASS** |
| process-group kill | a grandchild did **not** outlive the timeout (`grandchild_ran=False`) — **PASS** |

## M14.5 — live Action field test — **BLOCKED**

Running the composite Action against a **real PR** (patch artifact / `--publish`
branch, exit codes, the `always()` escalation step) needs an authenticated PR run and
opt-in secrets that cannot be produced in this environment. **Not** marked done on
static evidence. Evidence to date: the offline Action test
(`tests/meta/test_action.py`) plus the committed logs in `field-test/m10-action-e2e/`.

## Found issues (M14.8)

| # | Finding | Severity | Status |
|---|---|---|---|
| **F-1** | `markov-ci run` mapped a **compile-time config error** (e.g. no prior for the failure category) to an **unhandled traceback / exit 1** instead of **exit 4** (invalid config). Found while building the budget/isolation case. | P1 | **Fixed** in `0779334` — the loop-config build is now inside a `try` that maps `ConfigCompileError`/`ValueError` to `_fail` (exit 4). |
| **F-2** | `compose.yaml` demo expected exit codes were **stale** after the `a2: 2 → 1` contract change (demo-02/03 expected `2`), so `docker compose run` failed on a correct run. Found by the Docker field test. | P1 | **Fixed** in `0779334` — demo-02/03 now expect `1`. |

No open P0 findings. `F-1`/`F-2` are closed with the fixes above.

## Verdict

The v0.1.1 fixes hold outside the unit suite: the offline demos (CLI and Docker,
under `--network none`) reproduce their documented exit codes and byte-stable
seeded runs; FIX-01 payloads are inert; FIX-02 adversarial diffs are caught by the
guardrail before the sandbox; remaining-timeouts absorb in `a3` with an event; the
validation child gets a scrubbed environment; and a timed-out process tree is killed
whole. `M14.5` remains **blocked** on a live PR run.
