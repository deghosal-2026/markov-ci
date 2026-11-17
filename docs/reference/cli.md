# CLI reference

Normative contract: [spec/0008](../spec/0008-cli-contract.md). The exit-code table is
**stable API** — CI may branch on it.

## Global flags

| Flag | Default | Meaning |
|---|---|---|
| `--config PATH` | packaged default | config YAML (spec 0003) |
| `--seed INT` | — | deterministic RNG for `run` / `simulate` |
| `--json` | off | machine-readable output; same information as the human view |

## Commands

### `markov-ci validate [config]`
Validate + summarize the assembled matrix (states, augmentation, Q/R shape).
Exit `0` valid · `4` invalid — with the exact offending row, never a shrug.

### `markov-ci analyze [config] [--category C] [--json]`
Print `N` (expected visits), `B` (absorption probabilities), `t` (expected steps),
`C` (expected cost); credible intervals ship via `simulate`/`recompute`. Zero-config
works out of the box and prints the golden worked example (P(a1|s0) ≈ 0.92).

### `markov-ci run [config] --junit X [--seed S]`
Execute the governed remediation loop (spec 0011): triage → assemble → hop under the
policy gates → adapter repair → guardrails → sandbox → absorb.

### `markov-ci simulate [config] --runs N`
Monte-Carlo absorption/cost stats; must converge to the analytic `B`/`C` within
credible intervals (v0.2).

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
| `2` | absorbed in `a2_escalate_to_author` |
| `3` | absorbed in `a3_budget_exceeded` |
| `4` | invalid config / input — always explained, never silent |

## UX principles

1. Zero-config first run works.
2. Exit codes are a contract.
3. Human output via `rich`; machine output via `--json` — never parse prose.
4. Every printed number traces to config + telemetry — no magic constants.
5. The active adapter appears in every run header and event.
