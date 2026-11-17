# PRD — markov-ci (product requirements)

| Field | Value |
|---|---|
| **Product** | markov-ci — Markov-governed, self-healing CI/CD |
| **Version** | 0.8 (reviewed) |
| **Date** | 2026-11-16 |
| **Status** | Private, pre-implementation · release target v0.1.0 |
| **Owner** | @deghosal-2026 |
| **License** | Apache-2.0 |
| **Related docs** | [../OVERVIEW.md](../OVERVIEW.md) · [../spec/](../spec/README.md) · [../WBS.md](../WBS.md) |

**Revision history**

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-11-16 | First draft |
| 0.2 | 2026-11-16 | Deep rewrite: personas, MoSCoW F1–F28, metrics, release plan, traceability |
| 0.3 | 2026-11-16 | Harness-compatibility research applied: F19 → harness adapters; F29 MCP server; `adapter` telemetry field |
| 0.4 | 2026-11-16 | New "Why Markov" section |
| 0.5 | 2026-11-16 | Restructured into a folder of sub-PRDs; all content migrated |
| 0.6 | 2026-11-16 | World-class additions: Critical User Journeys, North Star metric, metric hierarchy, CUJ↔feature↔WBS traceability, GTM plan |
| 0.7 | 2026-11-16 | Dedicated **harness compatibility strategy** sub-PRD (07); security & privacy requirements (09); deprecation policy (10); files renumbered |
| 0.8 | 2026-11-16 | Gap review applied: **product principles** (00); NSM measurement resolution (03); **adoption ladder** (12 §6); APR + CI-observability competitive rows (11); sizing + dependency columns in the traceability matrix (13) |
| 0.9 | 2026-11-16 | Traceability re-synced to the tracked WBS: F20→M8.4, F22→M1.8, F19→M4.3–M4.4, F23–F29→M11.x, plus a GitHub-issue column (13 Appendix B) |
| 1.0 | 2026-11-16 | ADR chain completed (ADRs 0008–0010: triage-before-agents, guardrails-in-code, dual queueing); Appendix B gains an explicit **ADR** column so every feature is bound to its decision record |

## Sub-PRD index (read in order)

| # | Sub-PRD | Covers |
|---|---|---|
| 00 | [Product principles](00-principles.md) | The ten binding principles — they outrank features |
| 01 | [Summary and vision](01-summary-and-vision.md) | Executive summary, vision, positioning, the product test |
| 02 | [Problem and why Markov](02-problem-and-why-markov.md) | The problem, the opportunity, cost of inaction, **why Markov** |
| 03 | [Goals, metrics, non-goals](03-goals-and-metrics.md) | **North Star metric**, metric hierarchy, objectives, non-goals |
| 04 | [Users and stories](04-users-and-stories.md) | Personas and user stories with acceptance criteria |
| 05 | [Critical User Journeys](05-critical-user-journeys.md) | **CUJs** — end-to-end journeys per persona with success criteria |
| 06 | [Features — MUST](06-features-must.md) | The v0.1.0 blocker list (F1–F14), traced to CUJs |
| 07 | [Harness compatibility strategy](07-harness-compatibility.md) | Adapter tiers T1/T2/T3, supported harness matrix, MCP direction |
| 08 | [Features — SHOULD / COULD / WON'T](08-features-should-could-wont.md) | v0.2.0, v0.3+, and explicitly rejected scope |
| 09 | [UX, docs, quality, security](09-cli-ux-docs-quality.md) | CLI/UX, docs & content, quality attributes, security & privacy |
| 10 | [Release plan and constraints](10-release-and-constraints.md) | Release staging, deprecation policy, assumptions, constraints |
| 11 | [Risks and competition](11-risks-competitive-questions.md) | Risk register, competitive landscape, open questions |
| 12 | [Launch and GTM](12-launch-and-gtm.md) | Public flip sequencing, distribution, community, **adoption ladder**, validation loop |
| 13 | [Appendices](13-appendices.md) | Glossary, **CUJ ↔ feature ↔ ADR ↔ WBS ↔ issue matrix** with sizing + dependencies, spec contract map |

Stable IDs across all sub-PRDs: features F1–F29, objectives O1–O6, stories US-1…US-10,
journeys CUJ-1…CUJ-6, adapter tiers T1–T3 — referenced by [../WBS.md](../WBS.md) and
[../spec/](../spec/README.md).
