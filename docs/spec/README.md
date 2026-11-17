# markov-ci specifications

This folder holds the **numbered technical contracts** markov-ci is built against —
one contract per file, individually reviewable and versionable (KEP/OTEP convention).
The former monolithic `SPEC.md` was split into these files on 2026-11-16; all content
was migrated, nothing dropped.

- Product requirements: [../prd/](../prd/README.md) · Work plan: [../WBS.md](../WBS.md)
- Decision records: [../adr/](../adr/README.md)

## Index

| ID | Contract | Covers | Stability |
|---|---|---|---|
| [0001](0001-state-model.md) | State model | States, absorbing invariant, step augmentation, priors | **Stable** (v0.1 contract) |
| [0002](0002-matrix-assembly.md) | Matrix assembly & math | Canonical form, caps renormalization, `N`, `B`, `t`, `C`, CIs | **Stable** |
| [0003](0003-config-format.md) | Configuration format | Normative YAML schema + validation rules | Stable (new keys additive) |
| [0004](0004-policy-engine.md) | Policy engine | Gate order: budget → cap → confidence | **Stable** |
| [0005](0005-guardrails.md) | Guardrails | Allowlist, TMR checker, branch isolation, no-auto-merge | **Stable** |
| [0006](0006-agent-adapters.md) | Agent adapters | Adapter protocol, simulated agent, **harness adapters** | Experimental until v0.2 |
| [0007](0007-telemetry-events.md) | Telemetry events | Versioned JSONL event contract incl. `adapter` field | **Stable** (`schema_version` guards) |
| [0008](0008-cli-contract.md) | CLI contract | Commands, options, exit codes | **Stable** (exit codes are API) |
| [0009](0009-queueing.md) | Queueing | Erlang-C (M/M/c) + discrete-event simulator | Experimental until v0.2 |
| [0010](0010-triage.md) | Failure triage | JUnit/log classification, taxonomy, log minimizer | **Stable** |
| [0011](0011-engine-runtime.md) | Engine runtime | Transition loop, sandbox, RunResult | Stable |
| [0012](0012-engineering-baseline.md) | Engineering baseline | Packaging, compat, testing tiers, versioning policy | Stable |

**Reading order for a new contributor:** 0001 → 0002 → 0003 → 0004 → 0010 → 0006 →
0005 → 0011 → 0007 → 0008 → 0009 → 0012. (Numbers are chronological IDs, like ADRs;
the reading order differs on purpose.)

**Amending a contract:** contracts change via PR; supersede, don't silently rewrite —
bump the contract's `Amends` header. Anything marked *Experimental* may change before
its first tagged release; anything marked *Stable* follows semver + `schema_version`.

## Principles (binding on every contract)

1. **Markov-correct by construction.** Every matrix the engine executes is a true
   homogeneous Markov chain; attempt history lives in the state name, never in hidden
   counters. The fundamental-matrix math (`N = (I−Q)⁻¹`) therefore always applies.
2. **Absorption guaranteed.** Hard caps (step, token, wall-clock) make the chain
   absorbing even under adversarial or mis-estimated probabilities — `I−Q` invertible
   by construction; no run can loop forever.
3. **Guardrails are code.** Path allowlists, test-modification checks, branch isolation,
   and no-auto-merge are enforced in the engine, not in comments.
4. **Offline-first.** Every shipped demo runs with zero API keys. Real agents are opt-in
   harness adapters.
5. **Telemetry is a contract.** Events are schema-versioned JSON; the matrix can be
   recomputed from events alone, per failure category *and per agent adapter*.
6. **Determinism before intelligence.** No failure reaches an agent before a
   deterministic triage classifier has categorized it.
7. **markov-ci governs; it never delegates governance.** A harness's own allowlists or
   safety settings never substitute for markov-ci's guardrails.
