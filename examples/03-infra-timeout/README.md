# Example 03 — infra timeout, zero tokens

**Ships:** v0.1.0 · **Exit code to expect:** `1` · **Tutorial:** [03 — infra timeout](../../docs/tutorials/03-infra-timeout-no-tokens.md)

The "don't LLM the outage" story: some failures are *not code*, and the fastest agent is
the one that never runs. A registry timeout is classified deterministically and routed
straight to a human — **zero events, zero tokens**.

## Run it

```bash
markov-ci run examples/03-infra-timeout/config.yaml \
  --junit examples/03-infra-timeout/report.xml --seed 42
echo $?      # 1 = absorbed in a2_escalate_to_author
```

## Expected output

```
infra_timeout: matched 'timeouterror' → infra_timeout — escalating (a2)
```

Exit code `2`, and **no event stream is written**: triage runs *before* the governed
loop, so the run never reaches `s2`. The state space is the audit trail — there is
nothing to loop.

## What this proves

**Determinism before intelligence (principle 5).** A spot-instance interruption or a
registry `503` is not a code defect, and no amount of LLM reasoning fixes an AWS outage.
Triage classifies the signature (`TimeoutError`, `ConnectionRefused`, …) and routes to
`a2_escalate_to_author` before any adapter is constructed — so `tokens_used` is `0` and
no patch is ever proposed. The developer still receives the classified context (which
signature matched), not a shrug.

## Forecast vs. actual

The `infra_timeout` priors are `success: [0.05, 0.01, 0.00]` (spec 0001 §4) and
`min_confidence` is `0.40`, so the policy would reject attempt 1 anyway — triage simply
gets there first, skipping even the attempt-1 tokens (spec 0010 §4).

| Quantity | Forecast | this seeded run |
|---|---|---|
| attempt-1 confidence | 0.05 < 0.40 → would be rejected | never reached |
| absorbing state | `a2_escalate_to_author` | `a2_escalate_to_author` |
| events emitted | 0 (routed at triage) | 0 |
| tokens spent | 0 | 0 |

`dependency_error` follows the same route. Flip the fixture to a real `AssertionError`
and the same config routes to `s2#1` — the taxonomy, not luck, decides.
