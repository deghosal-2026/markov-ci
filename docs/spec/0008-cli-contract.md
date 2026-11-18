# Spec 0008 — CLI contract

**Status:** Stable — exit codes are public API (ADR-0017) · **Implements:** PRD F10

## 1. Commands

| Command | Purpose | Exit codes |
|---|---|---|
| `markov-ci validate [config]` | Validate + summarize the assembled matrix | 0 ok; 4 invalid |
| `markov-ci analyze [config] [--category C] [--json]` | Print `N`, `B`, `t`, `C` (CIs via `simulate`/`recompute`) | 0; 4 |
| `markov-ci run [config] --junit X [--seed S] [--repo P] [--adapter A] [--max-tokens N] [--wall-clock S]` | Governed remediation loop | 0 = a1; 1 = a2; 3 = a3; 4 invalid; 5 internal |
| `markov-ci simulate [config] --runs N` | Monte-Carlo absorption/cost stats | 0; 4 |
| `markov-ci queue --lambda L --mu M --c N [--simulate]` | Erlang-C (+ DES) runner-pool math | 0; 4 on bad input |
| `markov-ci recompute <events.jsonl>` | Empirical matrix from telemetry | 0; 4 |

## 2. Exit-code contract (stable across versions; CI may branch on it)

| Code | Meaning |
|---|---|
| 0 | Absorbed in `a1_ready_for_human_review` (or clean validation) |
| 1 | Absorbed in `a2_escalate_to_author` |
| 2 | **Reserved** — CLI usage error (Click); never a run outcome |
| 3 | Absorbed in `a3_budget_exceeded` |
| 4 | Invalid config / input — never a silent failure |
| 5 | Internal / infrastructure failure (mapped with a terminal event) |

> **Breaking change (v0.1.1, ADR-0017).** `a2` moved from `2` to `1`; `2` is Click's
> usage-error code. See the CHANGELOG.

## 3. Common argument & flags

- `[config]` — a **positional argument** on `validate` / `analyze` / `run` / `simulate`
  (default: the packaged default, spec 0003 §3). There is no `--config` flag.
- `--seed INT` — deterministic RNG for `run` / `simulate`.
- `--json` — machine-readable output (identical information to the human view);
  available on `analyze` / `run` / `simulate` / `queue` / `recompute`.

## 4. UX rules

1. Zero-config first run works: `markov-ci analyze` with no arguments prints the worked
   example (PRD F11).
2. Human output via `rich`; machine output via `--json`. No parsing prose in CI.
3. Every printed number is traceable to config + telemetry — no magic constants.
