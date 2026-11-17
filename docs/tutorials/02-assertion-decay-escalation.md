# Tutorial 02 — Assertion decay → escalation

**Demo:** `examples/02-unit-assertion-decay` · **Ships:** v0.1.0 · **Exit code to expect:** `2`

The guardrail story: a harder failure where the agent's odds decay per attempt until
the confidence gate says "stop" — *before* the third attempt burns tokens.

## Run it

```bash
markov-ci run examples/02-unit-assertion-decay/config.yaml \
  --junit examples/02-unit-assertion-decay/report.xml --seed 42
echo $?      # 2 = absorbed in a2_escalate_to_author
```

## What happens, hop by hop

`unit_assertion` priors: `success: [0.74, 0.45, 0.15]`, `min_confidence: 0.40`
(spec 0001 §4, spec 0004).

| Hop | State | Gate outcome |
|---|---|---|
| 1 | `s0 → s1 → s2#1` | classified `unit_assertion`; P(success) = 0.74 ≥ 0.40 → attempt 1 allowed |
| 2 | `s2#1 → s3#1` | patch proposed — sandbox says it did **not** fix the assertion |
| 3 | `s3#1 → s2#2` | loop back with the new error logs; P(success) = 0.45 ≥ 0.40 → attempt 2 allowed |
| 4 | `s2#2 → s3#2` | second patch — sandbox rejects again |
| 5 | `s3#2 → a2` | attempt 3 would carry P(success) = 0.15 < 0.40 → **confidence gate: escalate** |

Absorbed in `a2_escalate_to_author` — the developer gets the diagnostic context and
the full event trail; zero mystery, zero third-attempt spend.

## The math behind the stop

This is the step-augmented chain doing its job (ADR-0002): `s2#1`, `s2#2`, `s2#3` are
*distinct states* with their own edges, so per-attempt decay is ordinary Markov math —
`N`, `B`, `C` stay exact. Compare policies before you run them:

```bash
markov-ci analyze --category unit_assertion          # expected attempts + cost at max_attempts 3
```

Drop `min_confidence` to 0.10 and the forecast shows what attempt 3 would cost you —
that comparison *is* the "2 retries or 10?" debate, ended with a number (CUJ-1).

## What to notice

- Escalation is a **designed absorbing state**, not a crash: exit 2, full evidence.
- The event stream records both failed hops — `recompute` would *learn* from them
  (that's how priors become empirical, spec 0007 §4).
- Nothing ever retried forever: even `success: [1,1,1]` priors terminate — the cap
  makes absorption structural (ADR-0004).
