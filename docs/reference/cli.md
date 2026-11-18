# CLI reference

Normative contract: [spec/0008](../spec/0008-cli-contract.md). The exit-code table is
**stable API** — CI may branch on it.

## Common argument & flags

| Name | Where | Default | Meaning |
|---|---|---|---|
| `[config]` | `validate`, `analyze`, `run`, `simulate` | packaged default | config YAML — a **positional argument** (spec 0003) |
| `--seed INT` | `run`, `simulate` | `0` | deterministic RNG |
| `--json` | `analyze`, `run`, `simulate`, `queue`, `recompute` | off | machine-readable output; same information as the human view |

## Commands

### `markov-ci validate [config]`
Validate + summarize the assembled matrix (states, augmentation, Q/R shape).
Exit `0` valid · `4` invalid — with the exact offending row, never a shrug.

### `markov-ci analyze [config] [--category C] [--json]`
Print `N` (expected visits), `B` (absorption probabilities), `t` (expected steps),
`C` (expected cost); credible intervals ship via `simulate`/`recompute`. Zero-config
works out of the box and prints the golden worked example (P(a1|s0) ≈ 0.92 for all
builds, P(a1|s1) ≈ 0.54 for failed builds).

### `markov-ci run [config] --junit X [--seed S] [--repo P] [--adapter A] [--container-image I] [--max-tokens N] [--wall-clock S]`
Execute the governed remediation loop (spec 0011): triage → assemble → hop under the
policy gates → adapter repair → guardrails → worktree validation → absorb. `--repo` selects the
repository to validate in isolation; `--adapter` overrides `agent.adapter`; `--container-image`
runs validation in a container (`--network=none`, read-only checkout, tmpfs work dir, non-root;
ADR-0012); `--max-tokens` / `--wall-clock` override the config's policy budgets for this run;
`--output-patch FILE` writes the validated diff; `--publish` applies and pushes it to a fresh
`ai-fix/*` branch (never the PR branch, never `main`, never force). The composite Action's inputs
map straight onto these.

### `markov-ci simulate [config] --runs N`
Monte-Carlo absorption/cost stats. Its agreement with the analytic `B`/`C` is a
Monte-Carlo vs linear-algebra **consistency check**, not validation of the model (v0.2).

### `markov-ci queue --lambda L --mu M --c N [--simulate]`
Runner-pool math: `ρ`, `P_wait`, `Wq`, exact p95 for M/M/c; `--simulate` runs the
burst discrete-event simulator. `λ ≥ cμ` is refused with guidance (v0.2).

### `markov-ci recompute <events.jsonl>`
Empirical matrix from telemetry: counts → Dirichlet posterior + CIs → priors block
labeled `source: empirical` (v0.2).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | absorbed in `a1_ready_for_human_review` (or clean validation) |
| `1` | absorbed in `a2_escalate_to_author` |
| `2` | **reserved** — CLI usage error (Click); never a run outcome |
| `3` | absorbed in `a3_budget_exceeded` |
| `4` | invalid config / input — always explained, never silent |
| `5` | internal / infrastructure failure |

> **Breaking change (v0.1.1, [ADR-0017](../adr/0017-exit-code-contract.md)):** `a2` moved
> `2 → 1`; `2` is Click's usage-error code.

## UX principles

1. Zero-config first run works.
2. Exit codes are a contract.
3. Human output via `rich`; machine output via `--json` — never parse prose.
4. Every printed number traces to config + telemetry — no magic constants.
5. The active adapter appears in every run header and event.
