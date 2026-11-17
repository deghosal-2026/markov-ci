# Spec 0008 — CLI contract

**Status:** Stable — exit codes are public API · **Implements:** PRD F10

## 1. Commands

| Command | Purpose | Exit codes |
|---|---|---|
| `markov-ci validate [config]` | Validate + summarize the assembled matrix | 0 ok; 4 invalid |
| `markov-ci analyze [config] [--category C] [--json]` | Print `N`, `B`, `t`, `C` + CIs | 0; 4 |
| `markov-ci run [config] --junit X [--seed S]` | Governed remediation loop | 0 = a1; 2 = a2; 3 = a3; 4 invalid |
| `markov-ci simulate [config] --runs N` | Monte-Carlo absorption/cost stats | 0; 4 |
| `markov-ci queue --lambda L --mu M --c N [--simulate]` | Erlang-C (+ DES) runner-pool math | 0; 4 on bad input |
| `markov-ci recompute <events.jsonl>` | Empirical matrix from telemetry | 0; 4 |

## 2. Exit-code contract (stable across versions; CI may branch on it)

| Code | Meaning |
|---|---|
| 0 | Absorbed in `a1_ready_for_human_review` (or clean validation) |
| 2 | Absorbed in `a2_escalate_to_author` |
| 3 | Absorbed in `a3_budget_exceeded` |
| 4 | Invalid config / input — never a silent failure |

## 3. Global flags

- `--config PATH` — default: the packaged default (spec 0003 §3)
- `--seed INT` — deterministic RNG for `run`/`simulate`
- `--json` — machine-readable output; identical information to the human output

## 4. UX rules

1. Zero-config first run works: `markov-ci analyze` with no arguments prints the worked
   example (PRD F11).
2. Human output via `rich`; machine output via `--json`. No parsing prose in CI.
3. Every printed number is traceable to config + telemetry — no magic constants.
