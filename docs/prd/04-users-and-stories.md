# 04 — Users, personas, and user stories

## 1. Personas

### P1 — Platform/pipelines engineer ("Priya") — *primary*

- **Role:** owns CI fleet, runner capacity, budgets, org-wide pipeline standards.
- **Jobs to be done:** forecast agent rollout cost; guarantee no runaway; keep human PR
  latency flat; standardize retry/escalation policy org-wide.
- **Pains:** can't answer "2 retries or 10?" with data; agent validation bursts starve
  runners; fear of overnight bill shock.
- **Success:** runs `analyze` before enabling agents; pins policy in one shared YAML;
  sleep-at-night guarantee via absorbing caps.

### P2 — Application developer ("Marcus")

- **Role:** pushes PRs daily; wants fast, trustworthy greens.
- **Jobs:** trivial failures fixed without context-switch; clear escalation with
  diagnostics when agent can't; confidence that "green" still means green.
- **Pains:** hung PRs; agents weakening tests; opaque agent behavior.
- **Success:** first-time-to-green < 3 min on agent-fixable failures; every patch
  arrives on an isolated branch with a review summary; test-integrity flags visible.

### P3 — Agent/tooling builder ("Sam")

- **Role:** builds internal AI coding agents; wires them into CI.
- **Jobs:** plug an agent into a principled governance framework; get a thin, typed
  adapter protocol; demo it offline to stakeholders.
- **Pains:** bespoke retry YAML everywhere; no portable governance semantics; can't demo
  without API keys.
- **Success:** implements one protocol method; simulated + real adapters interchangeable;
  offline demo in CI.

### P4 — Engineering leader ("Dana")

- **Role:** accountable for delivery and spend.
- **Jobs:** see expected cost per PR before approving agent rollout; audit what agents
  actually did.
- **Success:** a one-page forecast (`analyze --json`) and an event stream that is the
  audit trail.

## 2. User stories and acceptance criteria

| # | Story | Acceptance criteria | Features |
|---|---|---|---|
| US-1 | As Priya, I want the expected cost/steps/outcomes of a pipeline before rollout, so I can approve agent spend. | `analyze` on default config prints N, B, t, C + CIs; matches golden numbers (P(a1\|s0) ≈ 0.92, P(a1\|s1) ≈ 0.54); `--json` machine-readable. | F1–F3, F10 |
| US-2 | As Priya, I want hard absorbing boundaries, so no run can loop forever. | Loop-cap edges removed at cap; e2e proves absorption on adversarial priors (success = [1.0,1.0,1.0] still absorbs). | F2, F4, F8 |
| US-3 | As Priya, I want runner-pool math for agentic bursts, so humans never starve. | Erlang-C ρ/P_wait/Wq/p95 + DES report; demo reproduces published numbers. | F16, F18 |
| US-4 | As Marcus, I want infra flakes to skip the agent, so no tokens are wasted. | `infra_timeout` classifies → immediate `a2`, zero tokens in demo 03. | F5, F8, F13 |
| US-5 | As Marcus, I want agent patches on an isolated branch, so my PR is never mangled. | Patch → `ai-fix/pr-<n>`; no force-push code path exists (test asserts); `a1` requires human merge. | F7, F8 |
| US-6 | As Marcus, I want tests protected from weakening, so a green suite still means the behaviour is tested. | Assertion-deleting patch → hard stop + mandatory-review flag; TMR > 1.0 → flag; blocks the textbook weakening patterns — a source-side special-case that leaves the assertion line in place is not detected. | F7 |
| US-7 | As Sam, I want to plug my harness (Claude Code, OpenCode, Aider, or my own) via one interface, so integration is trivial. | Protocol conformance suite; simulated and harness adapters pass the same tests. | F6, F19 |
| US-8 | As Sam, I want an offline reproducible demo, so I can show this in any meeting. | Demos 01–03 run with no network, seeded, byte-stable output. | F6, F13 |
| US-9 | As Dana, I want the token/cost forecast per category, so I can budget. | `analyze --category unit_assertion` shows per-attempt decay and expected spend; forecast vs simulated within CI. | F3, F4, F17 |
| US-10 | As Priya, I want the matrix to recompute from production telemetry, so guardrails adapt. | `recompute events.jsonl` → posterior matrix + CIs; round-trip golden test. | F9, F21 |
