# Architecture Decision Records (ADR)

One decision per file, numbered in decision order (MADR-lite format). ADRs are immutable
once accepted — supersede with a new ADR, never edit history. To add one: copy
[template.md](template.md), take the next number, open a PR.

| # | Decision | Status |
|---|---|---|
| [0001](0001-absorbing-markov-model.md) | Model pipelines as absorbing Markov chains | Accepted |
| [0002](0002-step-augmented-states.md) | Encode attempt count in the state name | Accepted |
| [0003](0003-simulated-agent-default.md) | Offline simulated agent is the default adapter | Accepted |
| [0004](0004-hard-caps-guarantee-absorption.md) | Hard caps guarantee absorption by construction | Accepted |
| [0005](0005-telemetry-versioned-contract.md) | Telemetry is a schema-versioned JSONL contract | Accepted |
| [0006](0006-src-layout-strict-typing.md) | src/ layout, `py.typed`, `mypy --strict` | Accepted |
| [0007](0007-harness-adapters-not-raw-sdks.md) | Real agents via headless harness CLIs, never raw SDKs | Accepted |
