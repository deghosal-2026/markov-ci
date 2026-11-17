# 10 — Release plan, assumptions, constraints, dependencies

## 1. Release plan

| Release | Theme | Scope | Public milestone |
|---|---|---|---|
| v0.1.0 | **Absorption** | F1–F14 (MUST) — math, policy, triage, simulated agent, guardrails, engine, telemetry, CLI, docs, demos 01–03 | Public flip + articles 1–2 |
| v0.2.0 | **Capacity & reach** | F15–F22 (SHOULD) — Action, queueing, simulate, recompute, demos 04–05, harness adapters (T2: Claude Code, OpenCode, Aider; T3: BYO) | Marketplace listing + article 3 |
| v0.3.0 | **Live operations** | F19 hardening, F23–F29 selectively (MCP governance server, community templates, currency costs, drift alerts) | Article 4 + community round |

Build order follows [../WBS.md](../WBS.md) (M0→M10); releases cut from the
MUST→SHOULD→COULD priority order, not the build order.

**Deprecation policy:** exit codes and event `schema_version` are stable API —
breaking changes require a major bump and one minor-release deprecation window.
`recompute` accepts all event versions ≤ current.

## 2. Assumptions

- Adopters have JUnit-style reports or plain logs (triage input).
- Teams want governance more than another harness.
- The source article's field numbers (0.82/0.18, 0.75/0.25, decay curves) are reasonable
  default priors until telemetry replaces them.
- Harness CLIs keep headless modes (currently true across the major five).

## 3. Constraints

- Private repo until the v0.1.0 gate; Apache-2.0; Python ≥ 3.11.
- No API keys in repo CI; all demos offline.
- Single-maintainer bandwidth — scope discipline is a survival constraint.
- Core carries no LLM/harness SDK dependency, ever (ADR-0007).

## 4. Dependencies

- **Runtime:** numpy, pydantic ≥ 2, PyYAML, typer, rich, jsonschema.
- **Dev:** pytest, hypothesis, ruff, mypy, mkdocs-material.
- **Ecosystem (T2 adapters, v0.2):** headless CLI availability of Claude Code, OpenCode,
  Aider; their version churn is a monitored dependency, not a blocker.
