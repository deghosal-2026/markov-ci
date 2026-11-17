# 03 — North Star metric, objectives, non-goals

## 1. North Star Metric

> **Governed runs per week** — the count of remediation loops executed under markov-ci
> governance (`markov-ci run` invocations that reach an absorbing state), summed weekly.

Why this one: it compounds all three value propositions in a single number. It grows
only when (a) someone adopted the tool, (b) the tool actually ran, and (c) the run
terminated in a designed outcome rather than a crash or a hang. `analyze`-only usage is
deliberately not counted — forecasting without governing is evaluation, not value.

## 2. Metric hierarchy

| Tier | Metric | Target |
|---|---|---|
| **North Star** | Governed runs / week | Trend line up post-public; reported in CHANGELOG |
| **Value (output)** | Absorbed-clean rate — % of agent runs reaching `a1` within budget | ≥ 70% |
| | First-pass resolution (S2→S3 on attempt 1) | 60–75% of eligible failures |
| | Forecast accuracy — actual spend vs analytic `C` | Within 10% |
| | Patch acceptance by developers | > 80% |
| **Guardrail** | Runaway compute incidents | **Zero** (structural, not aspirational) |
| | Test-integrity violations merged | **Zero** (TMR hard stop) |
| | Human PR queue wait p95 (demo fleet) | < 60 s |
| **Input (leading)** | Installs/clones · `analyze` runs · configs created · telemetry events/week · demo completions | Tracked, not targeted |

## 3. Product objectives

| # | Objective | Measured by | Target |
|---|---|---|---|
| O1 | Make agent governance computable | Forecast API + CLI shipped; docs derivation | v0.1.0 |
| O2 | Make runaway loops impossible | Structurally: hard caps ⇒ absorption by construction; e2e proves no infinite path | Zero runaway paths in tests |
| O3 | Work offline, reproducibly | All demos run with no API key, seeded RNG | 100% demos deterministic |
| O4 | Protect test-suite integrity | TMR checker + allowlist; adversarial fixtures | All adversarial fixtures blocked |
| O5 | Enable data-driven tuning | Telemetry contract + `recompute` | Round-trip reproduces matrix within CI |
| O6 | Build adoption through content | 4 published articles + public repo | 3–4 articles live post-release |

## 4. Engineering-quality metrics

| Metric | Target |
|---|---|
| Forecast accuracy (analytic `C` vs Monte-Carlo `simulate`) | Within CI at 95% |
| `validate` + `analyze` latency, ≤ 50 states | < 1 s |
| `simulate --runs 10000` | < 30 s |
| Engine overhead per state hop | < 5% of hop duration |
| Type/lint discipline | `mypy --strict` + `ruff` clean at every milestone gate |
| Python support | 3.11, 3.12, 3.13 |

## 5. Adoption signals (post-public; tracked, not targeted)

GitHub stars/clones, PyPI downloads, Action usage counts, article engagement,
external contributors, issue quality.

## 6. Non-goals (explicit out-of-scope, v0.x)

- ❌ **Agent hosting/harness.** markov-ci drives and governs existing harnesses
  (Claude Code, OpenCode, Aider, …) via adapters; it does not prompt, plan, or host agents.
- ❌ **Auto-merge.** Absorbing state `a1_ready_for_human_review` is terminal *by design*;
  humans merge.
- ❌ **CI-system replacement.** It plugs into GitHub Actions/GitLab/Jenkins.
- ❌ **Dashboard/UI.** CLI + JSON events; consumers build views.
- ❌ **Multi-chain modeling.** One pipeline = one chain in v0.x.
- ❌ **Guaranteed probability accuracy.** The model is only as good as its telemetry;
  we ship honest priors and confidence intervals, not guarantees about agent quality.
