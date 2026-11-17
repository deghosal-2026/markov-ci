# Design review: what the source article got right and wrong

markov-ci started from a public article on governing non-deterministic CI/CD with
Markov chains. The thesis is right; several mechanics are subtly broken. Each fix is
shipped in this repo and recorded as an ADR. This page is the honest errata — and the
seed for article #2.

## What it got right (kept as-is)

- **The core move:** model agentic pipelines as absorbing Markov chains; transient
  states (verify → triage → agent → sandbox → regression) and designed absorbing
  outcomes.
- **The canonical form** `P = [[Q, R], [0, I]]` and `N = (I − Q)⁻¹` as the expected-
  visits tool.
- **The operational patterns:** deterministic pre-triage (never route infra flakes to
  an LLM), state-scoped least privilege, telemetry→matrix recompute, bounded loops,
  no auto-merge, test-modification-ratio as anti-pattern #1.

## What it got wrong (and how markov-ci fixes it)

**1. Per-attempt decay silently breaks the math.** The article's example decays
success probabilities per retry step — a *time-inhomogeneous* chain for which
`N = (I−Q)⁻¹` does not apply, while still claiming exact expectations.
**Fix:** step-augmented states (`s2#1`, `s2#2`, …) restore a true homogeneous chain —
exact results, no special cases (ADR-0002).

**2. It promises "exact expected cost" but never defines it.** Only `N` is given;
`B = N·R` (outcome probabilities), `t = N·1` (steps), and `C = N·c` (cost) — the
actually decision-useful quantities — never appear.
**Fix:** all four ship as first-class `analyze` output, with golden-number tests.

**3. "Infinite loops" are misdiagnosed.** With exit probability > 0 on every loop, the
chain absorbs almost surely and `N` exists — the math was never in danger. The real
risks are the *cost tail* and a singular `I − Q` under mis-estimated (or adversarial)
probabilities. A runtime step counter treats the symptom after money burns.
**Fix:** caps remove loop-back edges at assembly time — absorption by construction,
an e2e test feeds `success = [1,1,1]` and asserts termination (ADR-0004).

**4. The `TRANSITION_MATRIX` conflates two things.** Keys are failure *categories* with
per-attempt *success curves* — a retry heuristic in Markov vocabulary, not a
transition matrix.
**Fix:** the state machine and its structural probabilities are one artifact; category
priors are a separate, labeled dimension resolved per *(category × adapter)*
(spec 0001, spec 0003).

**5. M/M/c is the wrong default for agent traffic — and p95 isn't Erlang-C.** The
article notes agent load is bursty, then models it Poisson; and Erlang-C yields
`P_wait`/mean wait, not p95 (that needs the wait-time distribution).
**Fix:** Erlang-C as the labeled quick estimator with the exact p95 formula, plus a
discrete-event simulator for bursty reality — convergence-tested against the closed
form (spec 0009).

**6. Point estimates with no uncertainty.** 10,000 runs of telemetry produce estimates
with real error bars; a FinOps forecast without intervals is false precision.
**Fix:** Dirichlet posteriors + credible intervals on every empirical number;
priors labeled `source: prior` vs `source: empirical` (spec 0002, spec 0007).

**7. Governance left as comments.** "Strict tool allowlists" and "never modify CI YAML"
appear in prose, not code.
**Fix:** guardrails are enforced in the engine — allowlist, TMR hard-stop, branch
isolation, an always-denied set that config cannot widen, and no force-push code path
(spec 0005, ADR "guardrails are code" principle).

## The one-line takeaway

The article's *insight* — pipelines are absorbing chains, so govern them with the
math — is correct and valuable. markov-ci is that insight made *rigorous*: exact where
the article approximated, structural where the article was procedural, and enforced
where the article advised.
