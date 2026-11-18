# WBS — markov-ci v0.1.1 ("Trust")

v0.1.1 closes the confirmed security holes found in the v0.1.0 review and makes the
product's claims match what the code does. It continues the v0.1.0 work breakdown
([WBS.md](WBS.md), M0–M11) — milestone IDs continue at **M12**, so commit/issue IDs
(`M12.1`, …) stay unique across the project.

**Source of scope:** the review under `markov-ci-cd/github/` (PRD-*, DES-*, ADR-*,
SRC-*, TEST-*, OPS-* findings) and the fix files FIX-01 … FIX-05.

v0.1.1 is organised as **four milestones**:

| Milestone | Content |
|---|---|
| **M12 — Documentation & claims** | every doc update the changes require: ADRs, spec sections, README/PRD/SECURITY.md wording, docs-enforcement tests |
| **M13 — Code changes** | every code, config, CI and test-suite change: FIX-01 … FIX-05 + test-suite hardening |
| **M14 — Field test** | raw, committed evidence that the fixes hold outside the unit suite |
| **M15 — Release readiness** | version bump, changelog, advisory, tag, publish, post-release checks |

**Sort rule.** A ticket whose deliverable is a document (ADR, spec section,
README/PRD wording, docs test) lives in **M12**. A ticket whose deliverable is code,
config, CI or test-suite behaviour lives in **M13**. Where one FIX item spanned both,
it is split and each half cross-references the other (only FIX-03 §6 needed this). The
`Source` column anchors every ticket back to the review folder; the re-sort map at the
end traces the earlier per-FIX draft IDs.

**Conventions (per team working rules):** one ticket at a time; test first (RED → GREEN);
run only the ticket's tests; each ticket ends implemented → tested → committed → pushed →
tracking issue closed. Ticket IDs are referenced in commits as `M<N>.<T>`.

**No skipped tests.** A test is either passing or failing — never skipped or conditionally
disabled. An enforcement test is written (RED) *with the artifact it guards*, never left as
a placeholder that skips until the artifact lands.

**Milestone gate (mandatory — every milestone M12–M15).** A milestone is **not complete**
until, on the merged milestone HEAD:

1. the **full test suite** passes (`make test`);
2. **≥ 95% coverage** of `src/markov_ci` passes (`make cov`, `--cov-fail-under=95`);
3. **`ruff` is clean** (`make lint`);
4. **`mypy --strict` is clean** (`make typecheck`).

`make gate` runs 2–4 together. Half-done is not done: a coverage dip below 95%, a ruff
finding, or a mypy error **blocks the milestone** — it is fixed before the milestone's
tracking issues are closed. No milestone closes with a red gate.

**Tracking:** every ticket below is a GitHub issue; each milestone maps to a GitHub
milestone. The `#` column is the issue number, created from this WBS.

---

## Release scope for v0.1.1

| Milestone | Source | Severity | v0.1.1 target |
|---|---|---|---|
| M12 — Documentation & claims | FIX-01…05 (doc halves) + ADR/PRD/OPS doc findings | High (credibility) | **Blocker** (safety notice + honest claims) |
| M13 — Code changes | FIX-01, FIX-02, FIX-04, FIX-05, FIX-03 + TEST findings | Critical → Low | **Blocker** (FIX-01, FIX-02, release pipeline) |
| M14 — Field test | — | — | **Blocker** (evidence for the release) |
| M15 — Release readiness | — | — | **Blocker** |

If time is short, the minimum shippable v0.1.1 is: the FIX-01 tickets (**M13.1–M13.6** +
M12.4, M12.7), the FIX-02 tickets (**M13.7–M13.12** + M12.5), the release-pipeline and
exit-code tickets (**M13.32–M13.35, M13.37** + M12.6), the patch artifact (**M13.23**),
the claims rewording (M12.8–M12.11), the snippet fix (M12.15), **all of M14** and **all of
M15**. Beyond the env scrub (M13.14) and the patch artifact (M13.23), the remaining FIX-04
isolation work — container isolation (M13.18) first — is the candidate to move to v0.2.0.

---

## M12 — Documentation & claims (all doc updates)

Every deliverable that is a document. The three decision ADRs (M12.1–M12.3) land **first**:
they decide what M13 implements. The mirrored contract docs (M12.4–M12.6) close immediately
after the code ticket they document; the wording sweep and docs-tests (M12.11, M12.19–M12.20)
close against the implemented code.

### Decisions (do first)

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.1 | FIX-04 §7 · ADR-14, ADR-15 | [#65](https://github.com/deghosal-2026/markov-ci/issues/65) | ADRs + threat model | write the sandbox/execution-isolation ADR and the trust-boundary/threat-model ADR: untrusted inputs (PR code, test output, agent output, repo rule files), assets (tokens, provider keys, repo, other branches), fork-PR policy, `pull_request_target`, token handling, `persist-credentials: false`. Gates M13.13–M13.19 |
| M12.2 | FIX-05 §1 · PRD-01 | [#66](https://github.com/deghosal-2026/markov-ci/issues/66) | Decide what "Markov-governed" means *(product)* | choose **A. Reposition** (runtime is a capped, guardrailed retry governor; the chain is a planning model) or **B. Make it true** (drive the loop from the assembled chain); record the choice as an ADR; update README, PRD-01 and `docs/architecture.md`. Gates M13.26–M13.28 and M12.8, M12.11 |
| M12.3 | FIX-05 §4 · ADR-18 | [#67](https://github.com/deghosal-2026/markov-ci/issues/67) | ADR: statistical estimation and learning | priors and prior strength, hierarchical pooling, drift/windowing, censoring and gated data, idempotent `recompute`. Gates M13.29 |

### Contract docs mirroring the code

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.4 | FIX-01 §5 · ADR-07, ADR-16 | [#68](https://github.com/deghosal-2026/markov-ci/issues/68) | FIX-01 docs + ADR | supersede/amend ADR-0007 (its `shell=True` / `%PROMPT%` note); update `docs/spec/0006-agent-adapters.md` §3, `docs/reference/configuration.md`, `docs/how-to/use-a-local-llm.md` to the argv contract (per M13.1–M13.4) |
| M12.5 | FIX-02 Docs · ADR-09 | [#69](https://github.com/deghosal-2026/markov-ci/issues/69) | FIX-02 docs | `docs/spec/0005-guardrails.md` §1: paths are derived from the diff, both sides of renames/deletes are checked, empty/unparseable diffs fail closed; add the consequence to ADR-0009; state the TMR known limitation (`assert f() == 2` → `assert True`) instead of implying it is caught (per M13.11) |
| M12.6 | FIX-03 §6 (docs half) · ADR-17, DES-29 | [#70](https://github.com/deghosal-2026/markov-ci/issues/70) | Exit-code contract docs | update spec 0008, `docs/reference/cli.md`, the `exit-code` description in `action.yml`; note the breaking change in the CHANGELOG; record the outcome-code semantics in an ADR (per M13.37) |

### Safety notice & honest claims

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.7 | FIX-01 Release actions · OPS-01 | [#71](https://github.com/deghosal-2026/markov-ci/issues/71) | Interim safety notice | README + `action.yml`: do not use `adapter: harness` on `pull_request` from untrusted authors until M13.18 (container isolation) lands |
| M12.8 | FIX-04 §3 (reword) · PRD-02, DES-01, ADR-04 | [#72](https://github.com/deghosal-2026/markov-ci/issues/72) | Reword the termination claim | README, PRD, ADR-0004: the **model** is acyclic after the cap (nilpotent `Q`); the **runtime** stops via an attempt counter plus per-call timeouts |
| M12.9 | FIX-05 §4 · SRC-08 | [#73](https://github.com/deghosal-2026/markov-ci/issues/73) | Label the priors illustrative | YAML comments, `analyze` output and docs; remove sentences that present them as typical measured behaviour |
| M12.10 | FIX-05 §4 | [#74](https://github.com/deghosal-2026/markov-ci/issues/74) | Stop calling simulation agreement "validation" | describe it as a Monte-Carlo vs linear-algebra check, nothing more |
| M12.11 | FIX-05 §7 + §2 numbers · PRD-04 | [#75](https://github.com/deghosal-2026/markov-ci/issues/75) | Wording sweep + golden numbers | apply the FIX-05 §7 table ("termination is a theorem" → model-acyclic + runtime counter/timeout; "self-healing" only once a patch is delivered; "sandbox" → "worktree validation"; "guardrails enforced in code" true only after M13.7–M13.12; "learns per harness" after M13.19); update README/tutorial/PRD numbers to the `s1` forecast rows per M13.26 |

### Doc & repo hygiene

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.12 | FIX-03 §7 · DES-15 | [#76](https://github.com/deghosal-2026/markov-ci/issues/76) | Correct the Erlang-C doc formula | add the missing factor `c` in `docs/explanations/queueing-theory.md`; optionally a docs test that evaluates the printed formula against `erlang_c()` |
| M12.13 | FIX-03 §9 · OPS-11, OPS-14 | [#77](https://github.com/deghosal-2026/markov-ci/issues/77) | Scrub paths + reconcile status | relativise the absolute paths in `field-test/`; reconcile the README status/roadmap with the CHANGELOG |
| M12.14 | OPS-09 | [#78](https://github.com/deghosal-2026/markov-ci/issues/78) | SECURITY.md accuracy | list what is enforced today vs aspirational (schema validation, "pinned" deps → lower-bounded, token caps, sandbox isolation) |
| M12.15 | FIX-03 §5 · OPS-04 | [#79](https://github.com/deghosal-2026/markov-ci/issues/79) | Fix the copy-paste workflows | point snippets at a real ref/SHA (not `@v0.2.0`); add `persist-credentials: false`, `setup-python`, `|| true` on the test step, and `if: always() && …` on the escalation step |

### ADR hygiene

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.16 | ADR-12 | [#80](https://github.com/deghosal-2026/markov-ci/issues/80) | ADR template: considered options | restore "Considered Options" and "Decision Drivers"; require ≥ 2 real options; add Deciders and a PR link |
| M12.17 | ADR-12 (top-5 #4) | [#81](https://github.com/deghosal-2026/markov-ci/issues/81) | Backfill options for ADR-0001/0004/0007/0009/0011 | each records a genuine alternative and why it lost |
| M12.18 | ADR-20, ADR-13 | [#82](https://github.com/deghosal-2026/markov-ci/issues/82) | Resolve the ADR↔spec drift | work the ADR-review contradiction table: superseding ADRs or `Amends:` spec amendments; never edit accepted ADRs in place |

### Docs-as-tests

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M12.19 | PRD-15, TEST-12, OPS-12 | [#83](https://github.com/deghosal-2026/markov-ci/issues/83) | Doc-consistency + docs-are-tests | count demos/ADRs and cross-check golden numbers across docs; fail (not filter) on a missing referenced path; compare golden-number output blocks against computed values |
| M12.20 | OPS-11 · FIX-03 §5 | [#84](https://github.com/deghosal-2026/markov-ci/issues/84) | Docs version-reference test | no `uses:` line references a version greater than `project.version` |

**Gate:** the three decision ADRs are accepted; ADR-0007 superseded/amended; spec
0005/0006/0008 sections match M13's behaviour; no claim in README/PRD/SECURITY.md exceeds
what the code does; docs-consistency and version-reference tests green · ≥95% coverage ·
`ruff` + `mypy --strict` clean.

---

## M13 — Code changes (all code, config, CI and test changes)

Every deliverable that changes what the code does. Grouped by FIX, in the order they run.

### FIX-01 — argv-only harness invocation · [Critical] — closes SRC-01, TEST-01, OPS-01, PRD-03. Blocks the release.

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.1 | FIX-01 §1 · SRC-01 | [#85](https://github.com/deghosal-2026/markov-ci/issues/85) | argv-only invocation | `HarnessAgent` splits `command_template` with `shlex.split` **before** substituting `%PROMPT%`; the prompt becomes a single argv element; run `subprocess.run(argv, shell=False)`; drop the ad-hoc `"` → `\"` escaping |
| M13.2 | FIX-01 §2 | [#86](https://github.com/deghosal-2026/markov-ci/issues/86) | Validate the template at config load | reject empty, unparseable (unbalanced quotes), missing `%PROMPT%`, and `%PROMPT%` as the program name; fails as invalid config (exit **4**), not exit 2 mid-run |
| M13.3 | FIX-01 §3 | [#87](https://github.com/deghosal-2026/markov-ci/issues/87) | Reject shell re-entry | reject `argv[0] ∈ {sh,bash,zsh,dash,pwsh,powershell,cmd}` when `%PROMPT%` appears after `-c` / `/c`; allow the safe positional form (`bash -c 'tool "$1"' _ %PROMPT%`) |
| M13.4 | FIX-01 §4 | [#88](https://github.com/deghosal-2026/markov-ci/issues/88) | Prompt off argv (follow-up) | optional `%PROMPT_FILE%` (temp file, `0600`) or stdin, so the prompt never appears in `ps`/ARG_MAX; documented alongside argv substitution (M12.4) |
| M13.5 | FIX-01 Tests · TEST-01 | [#89](https://github.com/deghosal-2026/markov-ci/issues/89) | Adversarial regression suite | run through the **real** `_default_runner` with a harmless echo program: `$(…)`, backticks, the `\"` breakout, `;`, `|`, `&&`, newline, `$HOME`, `'`/`"` must reach the child verbatim with **no marker file**; hypothesis property: the parsed argv contains the prompt byte-for-byte |
| M13.6 | FIX-01 §5 | [#90](https://github.com/deghosal-2026/markov-ci/issues/90) | Remove the `# nosec B602` | bandit guards the call again; no `shell=True` anywhere in `src/` |

### FIX-02 — guardrails: derive paths from the diff · [High] — closes SRC-02, SRC-11, SRC-12, TEST-02, TEST-03. Blocks the release.

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.7 | FIX-02 §1 · SRC-02 | [#91](https://github.com/deghosal-2026/markov-ci/issues/91) | Diff path parser (engine) | parse `diff --git`, `---`/`+++`, `rename from/to`, `copy from/to`; collect **both** old and new paths; drop text after a tab; skip `/dev/null`; strip the first path component (`-p1`); unescape git C-style quoted paths (`\\`, `\"`, `\t`, `\n`, octal `\NNN`) before matching |
| M13.8 | FIX-02 §2 | [#92](https://github.com/deghosal-2026/markov-ci/issues/92) | Check the union, fail closed | check derived ∪ declared paths; a non-empty diff with no derivable paths denies (`could not determine the paths this patch touches`); a symlink creation (`mode 120000`) denies and is recorded in the guardrail report |
| M13.9 | FIX-02 §3 | [#93](https://github.com/deghosal-2026/markov-ci/issues/93) | Post-apply verification | after `git apply` and before the test command, re-run the allowlist on `git diff --name-status -M` in the worktree, so git is the source of truth |
| M13.10 | FIX-02 Tests · TEST-02 | [#94](https://github.com/deghosal-2026/markov-ci/issues/94) | Property test vs real git | for any generated diff, every path git reports as touched is caught by the engine's parser |
| M13.11 | FIX-02 §4 · TEST-03 | [#95](https://github.com/deghosal-2026/markov-ci/issues/95) | TMR uses the same parsed data | classify a deleted file by its **original** path; a deleted test file counts as test lines; cover the ratio boundary of exactly `1.0` (spec wording per M12.5) |
| M13.12 | FIX-02 §5 · SRC-12 | [#96](https://github.com/deghosal-2026/markov-ci/issues/96) | Harden the always-denied set | deny `.env*` / `**/.env*`, CI + build config for common systems, `CODEOWNERS`, credentials/keys; match case-insensitively; replace the hand-rolled glob translator with `pathspec` (gitignore semantics) |

### FIX-04 — isolation, hard budgets, delivering the patch · [High] — closes SRC-03, SRC-04, SRC-05, SRC-09, SRC-10, OPS-02, OPS-03, PRD-02. ADRs first (M12.1).

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.13 | FIX-04 §1.1 · SRC-03 | [#97](https://github.com/deghosal-2026/markov-ci/issues/97) | Rename until it is real | "worktree validation" in code, docs, README and PRD; "sandbox" no longer promises isolation that does not exist |
| M13.14 | FIX-04 §1.2 | [#98](https://github.com/deghosal-2026/markov-ci/issues/98) | Scrub the environment | pass an allowlisted env (`PATH`, `HOME` → temp, `LANG`, plus config-listed vars); drop `GITHUB_TOKEN`, `ACTIONS_*`, `*_TOKEN` / `*_KEY` / `*_SECRET` |
| M13.15 | FIX-04 §1.3 | [#99](https://github.com/deghosal-2026/markov-ci/issues/99) | Kill the whole process tree | `start_new_session=True` + `os.killpg` on timeout (Job Object on Windows); bound captured output (last 1 MB) |
| M13.16 | FIX-04 §1.4 | [#100](https://github.com/deghosal-2026/markov-ci/issues/100) | Resource limits | `resource.setrlimit` (CPU, address space, file size) in `preexec_fn` on POSIX |
| M13.17 | FIX-04 §1.5 | [#101](https://github.com/deghosal-2026/markov-ci/issues/101) | Do not share the repo's git state | clone into the temp dir (`git clone --no-hardlinks --local`) instead of `git worktree add`, so hooks, config and credentials are not shared; clean up via a context manager |
| M13.18 | FIX-04 §1.6 | [#102](https://github.com/deghosal-2026/markov-ci/issues/102) | Container isolation option | run validation in a container (`--network=none`, read-only checkout, tmpfs work dir, non-root); make it the default in the Action for fork PRs |
| M13.19 | FIX-04 §2 · SRC-04, OPS-02 | [#103](https://github.com/deghosal-2026/markov-ci/issues/103) | Harness runs in the validation copy | pass `cwd`; derive the proposal as `git diff` of that tree, not from parsed stdout; scrubbed env with only the needed key; set `HarnessSpec.id` from the template name (today every harness reports `adapter="harness"`) |
| M13.20 | FIX-04 §3 · SRC-09, PRD-02 | [#104](https://github.com/deghosal-2026/markov-ci/issues/104) | Remaining-budget timeouts | pass `min(configured_timeout, remaining_wall_clock)` to every harness and sandbox call; a timeout absorbs in `a3` **with an event** |
| M13.21 | FIX-04 §3 (tokens) | [#105](https://github.com/deghosal-2026/markov-ci/issues/105) | Real token accounting | parse each harness's real usage output (e.g. `claude -p --output-format json` `usage`); unknown usage → `tokens_used=null` and stated in the run result; document that the token cap binds only for adapters that report usage |
| M13.22 | FIX-04 §3 (events) | [#106](https://github.com/deghosal-2026/markov-ci/issues/106) | Terminal event on every exit | via a `finally`: ineligible triage, harness error, timeout and uncaught exception all emit a terminal event; align exit code and event stream |
| M13.23 | FIX-04 §4 · SRC-05, OPS-03 | [#107](https://github.com/deghosal-2026/markov-ci/issues/107) | Persist the validated patch | `RunResult.patch` / `patch_path` + `--output-patch FILE`; upload it as an Action artifact next to `events.jsonl`; `a1` no longer discards the fix |
| M13.24 | FIX-04 §4 (publish) · PRD-08 | [#108](https://github.com/deghosal-2026/markov-ci/issues/108) | Opt-in publish | `--publish` / Action `publish: true`: apply **exactly** the validated diff to a fresh branch from the PR head; commit only those paths (never `git add -A`); assert `git diff --name-only` equals the validated path set; push without force; report `patch_branch` only after a successful push, else `null`; e2e test asserts the branch exists and its diff matches |
| M13.25 | FIX-04 §5 · SRC-10 | [#109](https://github.com/deghosal-2026/markov-ci/issues/109) | Retries carry new information | feed the minimized + scrubbed validation output and the previous diff into the next `RepairContext`; log a summarized `SandboxResult.output` so "agent failed" is distinguishable from "test command not found" / "not a git repo" |

### FIX-05 — model ↔ runtime consistency · [High (credibility)] — closes SRC-06, SRC-07, SRC-08, SRC-15, SRC-18, PRD-01, PRD-04, PRD-05. Decision first (M12.2, M12.3).

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.26 | FIX-05 §2 · SRC-07 | [#110](https://github.com/deghosal-2026/markov-ci/issues/110) | Forecast from `s1` | default the start state to `s1` (the engine only runs after a failure) and add `--start STATE`; print both rows, labelled "all builds" (`s0`) and "failed builds" (`s1`) — README/tutorial/PRD numbers per M12.11 |
| M13.27 | FIX-05 §3 · DES-04 | [#111](https://github.com/deghosal-2026/markov-ci/issues/111) | Model the confidence gate | during assembly, zero the `s2#k` edge and send its mass to the escalation sink when `success[k] < min_confidence`; warn when `max_attempts` is unreachable; property test that the Monte-Carlo of the engine policy agrees with the analytic `B` per category |
| M13.28 | FIX-05 §3 (a3) · DES-03 | [#112](https://github.com/deghosal-2026/markov-ci/issues/112) | Make `P(a3)` honest | either add budget-overrun edges, or label `P(a3)` in output as "not modelled — `simulate` only" (depends on M13.20) |
| M13.29 | FIX-05 §4 (recompute) · SRC-08, DES-12 | [#113](https://github.com/deghosal-2026/markov-ci/issues/113) | Fix `recompute` and event fidelity | each estimated quantity maps to exactly one edge; CLI passes the config prior and `alpha`; tag simulated events `synthetic: true` and exclude them by default; record gate rejections as `gate_rejected` (with reason); add `config_hash` and `model_version` to events |
| M13.30 | FIX-05 §5 · SRC-15 | [#114](https://github.com/deghosal-2026/markov-ci/issues/114) | Config validation holes | reject prior `success` outside `[0, 1]` at load; `validate` checks every matrix entry lies in `[0, 1]`; check the config `version` before the pydantic schema |
| M13.31 | FIX-05 §6 · SRC-18 | [#115](https://github.com/deghosal-2026/markov-ci/issues/115) | Dead config and dead code | use or remove `cost_weight`; pass the real adapter id; wire `TEMPLATES` / `build_template_agent` (or stop advertising named templates); remove the empty `harness` extra; move `failing_command` / `regression_command` / `pr_number` into config + Action inputs; require an explicit broader regression command or skip `s4` |

### FIX-03 — release pipeline, contract & repo hygiene · [High→Low] — closes OPS-04, OPS-05, OPS-06, OPS-11, TEST-05, TEST-09 + addendum spot-checks. Items 1–3 and 6 block v0.1.1.

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.32 | FIX-03 §1 · OPS-05 | [#116](https://github.com/deghosal-2026/markov-ci/issues/116) | Tests gate the release | add a `test` job to `release.yml` (3.11–3.13 matrix, lint, mypy, coverage) and make `build` `needs: [gate, test]` |
| M13.33 | FIX-03 §1 (tag check) | [#117](https://github.com/deghosal-2026/markov-ci/issues/117) | Tag/version + main check | fail the release unless the tag equals `project.version` and the tagged commit is on `main` |
| M13.34 | FIX-03 §2 | [#118](https://github.com/deghosal-2026/markov-ci/issues/118) | Trusted Publishing | configure a PyPI Trusted Publisher; remove `password:`; delete and revoke the token; run `publish` in a protected `environment: pypi`; grant `id-token: write` only there; add `actions/attest-build-provenance` on `dist/*` |
| M13.35 | FIX-03 §3 · OPS-06 | [#119](https://github.com/deghosal-2026/markov-ci/issues/119) | Pin actions by SHA | every `uses:` → full 40-char SHA with a version comment; add `.github/dependabot.yml` (github-actions, pip); pin `action.yml`'s `upload-artifact` too |
| M13.36 | FIX-03 §4 · TEST-05 | [#120](https://github.com/deghosal-2026/markov-ci/issues/120) | Coverage enforced in CI | `pytest --cov=markov_ci --cov-branch --cov-fail-under=95` in `ci.yml`; `branch = true`; state line-vs-branch in spec 0012; scheduled mutation job (`mutmut`/`cosmic-ray`) on `policy/`, `guardrails/`, `engine/` with a kill-rate floor |
| M13.37 | FIX-03 §6 (code half) · DES-29 | [#121](https://github.com/deghosal-2026/markov-ci/issues/121) | Fix the exit-code contract | move a2/a3 off Click's reserved `2`; add a code for internal/infra failure; catch all exceptions → documented code + terminal event; update the `BY_CODE` map in `action/run.sh` (spec 0008, CLI reference, ADR per M12.6) |
| M13.38 | FIX-03 §8 · TEST-09 | [#122](https://github.com/deghosal-2026/markov-ci/issues/122) | Untrack the runtime artifact + hermetic tests | `git rm --cached .markov-ci/events.jsonl`; ignore `.markov-ci/`; tests write telemetry to `tmp_path`; copy example repos to `tmp_path` before `git init`; CI asserts `git status --porcelain` is empty after the suite |

### Test-suite hardening — closes TEST-04, TEST-06…TEST-08, TEST-10, TEST-11, TEST-14, TEST-15, TEST-16

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M13.39 | TEST-04/06/07/08/10/11/16 | [#123](https://github.com/deghosal-2026/markov-ci/issues/123) | Test-suite hardening | exact wall-clock boundary and precedence; regression failure → `a2`; property tests over random state spaces (assert nilpotent `Q` or `UNREACHABLE_ABSORPTION`); adversarial allowlist cases under `allow_write=("**",)`; JUnit size cap + XXE / billion-laughs fixtures; `sys.executable` in the Action test; e2e golden event streams compared against the README; pin posterior numbers to independent values |
| M13.40 | TEST-14 | [#124](https://github.com/deghosal-2026/markov-ci/issues/124) | Honest repo-shape tests | move the ~70 meta tests into `tests/meta/`; parse YAML (matrix, `--cov-fail-under`) instead of substring greps; add `actionlint` / `hadolint` |
| M13.41 | TEST-15 | [#125](https://github.com/deghosal-2026/markov-ci/issues/125) | Remove tautological tests; prove offline | delete or make real the redundant tests; block sockets with an autouse fixture so the whole suite proves it runs offline |

**Gate:** no `shell=True` in `src/`; every injection payload is inert through the real
runner; template validation exits 4; deleting `.github/workflows/ci.yml`, renaming into
`.github/`, and a quoted escaped path (`\056github`) all end in `a2` with a guardrail
report and the sandbox is **never invoked**; the diff-path property test is green; a
deleted test file is classified as test lines; env-scrub, process-group, rlimit and clone
tests green; every exit path emits a terminal event; with `--publish`, `a1` produces a
branch whose diff equals the validated diff (without it, a patch file); the release
workflow runs the full suite and fails on a red tag; Trusted Publishing is configured; all
actions SHA-pinned; the coverage gate runs in CI; `git status` is clean after the suite ·
≥95% coverage · `ruff` + `mypy --strict` clean.

---

## M14 — Field test (v0.1.1)

Raw, committed evidence that the fixes hold outside the unit suite — mirroring the v0.1.0
`field-test/m9-examples` and `field-test/m10-action-e2e` layout. Runs after M12 + M13.

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M14.1 | was M18.1 | [#126](https://github.com/deghosal-2026/markov-ci/issues/126) | Protocol + harness | define `field-test/v0.1.1/` (raw logs + a README summary naming environment, commit and version); a runner script that captures exit codes and event streams |
| M14.2 | was M18.2 | [#127](https://github.com/deghosal-2026/markov-ci/issues/127) | Offline proof suite | re-run demos 01–07 and the Docker runner under `--network none`; confirm documented exit codes, event streams and `--seed` byte-stability |
| M14.3 | was M18.3 | [#128](https://github.com/deghosal-2026/markov-ci/issues/128) | Injection field test | run the FIX-01 payloads against the real runner on a clean checkout; assert no marker file is created; commit the evidence |
| M14.4 | was M18.4 | [#129](https://github.com/deghosal-2026/markov-ci/issues/129) | Guardrail field test | run the FIX-02 adversarial diffs (delete/rename CI config, quoted escaped paths) through a real git repo; each ends `a2` with a guardrail report and the sandbox is never invoked |
| M14.5 | was M18.5 | [#130](https://github.com/deghosal-2026/markov-ci/issues/130) | Live Action field test | run the composite Action against a real PR (opt-in secrets); verify the patch artifact / publish branch (M13.23/M13.24), exit codes, and the `always()` escalation step; capture logs + run metadata |
| M14.6 | was M18.6 | [#131](https://github.com/deghosal-2026/markov-ci/issues/131) | Budget & isolation field test | confirm a remaining-time timeout absorbs in `a3` with an event (M13.20); confirm the scrubbed env hides `GITHUB_TOKEN` (M13.14); confirm the process-group kill (M13.15) |
| M14.7 | was M18.7 | [#132](https://github.com/deghosal-2026/markov-ci/issues/132) | Field-test report | `field-test/v0.1.1/FIELD_TEST_REPORT.md` — per-case P/F, found issues, and a **hand-maintained** note (no automation may overwrite it) |
| M14.8 | was M18.8 | [#133](https://github.com/deghosal-2026/markov-ci/issues/133) | Fix-or-file | every failure is filed as a ticket; release readiness is blocked on open P0 findings |

**Note:** cases that need a real runner or authenticated captures are marked **blocked** if
they cannot be produced here — never marked done on static evidence.

**Gate:** the report is committed with all P0 findings closed or explicitly blocked;
the injection and guardrail field tests show no bypass · ≥95% coverage ·
`ruff` + `mypy --strict` clean.

---

## M15 — Release readiness (v0.1.1)

| ID | Source | # | Ticket | Deliverable / acceptance |
|---|---|---|---|---|
| M15.1 | was M19.1 | [#134](https://github.com/deghosal-2026/markov-ci/issues/134) | Version bump | `0.1.1` in `pyproject.toml` and `__init__.py` (guarded by the version test) |
| M15.2 | was M19.2 | [#135](https://github.com/deghosal-2026/markov-ci/issues/135) | CHANGELOG `[0.1.1]` | Keep a Changelog sections: **Security** (shell-injection fix + advisory reference), **Fixed**, **Changed** |
| M15.3 | was M19.3 | [#136](https://github.com/deghosal-2026/markov-ci/issues/136) | Security advisory | open a private GitHub Security Advisory for `0.1.0`; yank `0.1.0` or ship `0.1.1` as the patch; state it in the release notes |
| M15.4 | was M19.4 | [#137](https://github.com/deghosal-2026/markov-ci/issues/137) | Release security & supply-chain gate | re-run the history secret scan, `pip-audit`, `bandit`, license check and SBOM + attestations on the release commit |
| M15.5 | was M19.5 | [#138](https://github.com/deghosal-2026/markov-ci/issues/138) | Tag + GitHub Release | tag `v0.1.1` on `main`; GitHub Release; publish to PyPI via **Trusted Publishing** (M13.34) |
| M15.6 | was M19.6 | [#139](https://github.com/deghosal-2026/markov-ci/issues/139) | Post-release verification | install from PyPI in a clean venv; `analyze` from `s1`; Action smoke test; confirm build provenance is present |
| M15.7 | was M19.7 | [#140](https://github.com/deghosal-2026/markov-ci/issues/140) | Update release docs | reconcile the PRD 10 release-plan table and the roadmap with what shipped; close the milestone |

**Gate:** v0.1.1 installs from PyPI and runs; the advisory/yank is handled; the release
security gate is green; the field-test report shows all P0 fixed · ≥95% coverage ·
`ruff` + `mypy --strict` clean.

---

## Order of work and dependencies

One ticket at a time, in this order:

1. **Decisions first (M12.1–M12.3).** The sandbox/trust-boundary ADRs, the
   "Markov-governed" product decision and the estimation ADR decide what M13 implements.
   M12.2 is the one **product decision**; it gates M13.26–M13.28 and the
   README/PRD/architecture wording (M12.8, M12.11).
2. **Code (M13), in FIX order:** FIX-01 (M13.1–M13.6) → FIX-02 (M13.7–M13.12) →
   FIX-04 (M13.13–M13.25) → FIX-05 (M13.26–M13.31) → FIX-03 (M13.32–M13.38) →
   test-suite hardening (M13.39–M13.41).
   - `M13.1–6 → M13.7–12`: the harness must be argv-only before the diff-derived path
     check is the authority.
   - `M13.7–9 → M13.19`: M13.19 derives the proposal from the worktree diff that the
     derived-path check validates.
   - `M13.20 → M13.28`: budget edges and honest `P(a3)` depend on the budget work.
   - `M13.37 ↔ M12.6`: the exit-code contract is a breaking change; spec, CLI reference
     and ADR land with the code.
   - Each mirrored contract doc (M12.4–M12.6) closes immediately after the code ticket
     it documents.
3. **Docs & claims (the rest of M12)** close against the implemented code: the wording
   sweep (M12.11) and the docs-as-tests (M12.19–M12.20) reference shipped behaviour and
   golden numbers.
4. **Field test (M14)** after M12 + M13.
5. **Release readiness (M15)** after M14.

## Re-sort map (earlier draft → this WBS)

The earlier per-FIX draft (M12–M19, never issued) is retired. Every ticket maps 1:1,
except FIX-03 §6, split into its code and doc halves:

- old M12.1–M12.6 → **M13.1–M13.6** · old M12.7 → **M12.4** · old M12.8 → **M12.7**
- old M13.1–M13.6 → **M13.7–M13.12** · old M13.7 → **M12.5**
- old M14.1–M14.13 → **M13.13–M13.25** · old M14.14 → **M12.1** · old M14.15 → **M12.8**
- old M15.1 → **M12.2** · old M15.2 → **M13.26** (+ numbers → M12.11) ·
  old M15.3–M15.4 → **M13.27–M13.28** · old M15.5 → **M12.9** · old M15.6 → **M12.10** ·
  old M15.7–M15.9 → **M13.29–M13.31** · old M15.10 → **M12.11** · old M15.11 → **M12.3**
- old M16.1–M16.5 → **M13.32–M13.36** · old M16.6 → **M13.37 + M12.6** (split) ·
  old M16.7 → **M12.15** · old M16.8 → **M13.38** · old M16.9 → **M12.12** ·
  old M16.10 → **M12.13** · old M16.11 → **M12.14**
- old M17.1–M17.5 → **M12.16–M12.20** · old M17.6–M17.8 → **M13.39–M13.41**
- old M18.1–M18.8 → **M14.1–M14.8** · old M19.1–M19.7 → **M15.1–M15.7**

## Definition of done (per ticket)

Implemented · test passing · committed · pushed · tracking issue closed. Anything else
("implemented but uncommitted", "core slice") is **not** done and is reported as not done.
