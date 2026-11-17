# Spec 0004 — Policy engine

**Status:** Stable (v0.1 contract) · **Amends:** — · **Implements:** PRD F4

## 1. Policy

```python
@dataclass(frozen=True)
class Policy:
    min_confidence: float = 0.40      # reject transition if P(success) below
    max_attempts: int = 3            # step cap → absorption by construction
    max_tokens: int = 200_000        # absorbing a3 if exceeded
    wall_clock_seconds: int = 900    # absorbing a3 if exceeded
```

## 2. Evaluation order (strictly ordered, never reordered)

Per transition decision, evaluated in this order — first match wins:

1. **Budgets** — `tokens_used > max_tokens` or elapsed > `wall_clock_seconds` → `a3_budget_exceeded`.
2. **Attempt cap** — attempt would exceed `max_attempts` → `a2_escalate_to_author`.
3. **Confidence threshold** — resolved P(success) for the next attempt < `min_confidence` → `a2`.
4. **Transition** — proceed per the matrix (seeded RNG in simulated mode; executed
   reality in live mode).

Every rejection lands in a *designed* absorbing state — there is no "uncategorized" exit.

## 3. Notes

- The engine never treats a prior's `success[k]` as a live probability: live runs use
  the *executed outcome*; the matrix governs *expectations* and *gate decisions*.
- Caps feed back into assembly: `max_attempts` determines which loop-back edges are
  removed (spec 0002 §1.3) — policy and matrix stay consistent by construction.
