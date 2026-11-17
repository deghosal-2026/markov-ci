# 02 — The problem, the opportunity, and why Markov

## 1. The problem, precisely

1. **The DAG assumption is dead.** Same commit ≠ same result: network jitter, CPU
   contention, spot interruptions, registry 503s. And agents — the second and bigger
   force — are stochastic: fix 75% / loop 15% / regress 10% is typical field behavior.
2. **Deterministic governance of probabilistic systems fails.** Strict rules → agent
   never useful; loose rules → unbounded retries.
3. **The pain is already concrete** (evidence from the field-test literature this product
   is based on):
   - overnight agent loops → cloud/token bill shock;
   - agent sandbox runs saturate shared runners → humans wait, context-switch, lose flow;
   - agents "fix" tests by weakening assertions → green build, dead test suite;
   - retry counts, escalation thresholds, and budgets are chosen by gut, never computed;
   - no telemetry to say whether agentic CI helped or hurt.

## 2. The opportunity

- Absorbing Markov chains are 100-year-old, textbook mathematics that map **exactly**
  onto "pipeline states + terminal outcomes." Nobody has packaged this as reusable
  CI/CD infrastructure.
- Agent adoption in CI is happening **now**; the governance layer is the missing piece
  between agent harnesses (which act) and CI systems (which execute).
- First credible open-source implementation + a documented model + articles = category
  definition ("Markov-governed CI").

## 3. Cost of inaction (for adopters)

Teams without a governance model pay in runaway spend, silently corrupted test suites,
and unpredictable PR latency — all discovered after the fact, none forecastable.

## 4. Why Markov — what Markov has to do with CI/CD

A Markov chain is a system that hops between discrete states, where the probability of
the next hop depends only on the current state. An agentic CI pipeline **already is**
that system — the model doesn't approximate the pipeline, it names what the pipeline
has become:

- **Discrete states:** verify → triage → agent-reasoning → sandbox → regression → outcome.
- **Probabilistic hops:** a patch passes validation ~65% of the time, a regression check
  ~90% — the hop is a coin weighted by reality, not a rule.
- **Termination:** every run ends — ready-for-review, escalated, or budget-stopped.
  Termination makes this an *absorbing* Markov chain: the branch of the theory built
  precisely for "systems that eventually stop."

Because the pipeline already has this shape, textbook results become product features:

| Math | Formula | What it answers |
|---|---|---|
| Fundamental matrix | `N = (I−Q)⁻¹` | Expected agent attempts, runner-minutes, tokens per run |
| Absorption probabilities | `B = N·R` | What % of runs ship vs. escalate vs. hit the budget wall |
| Steps to absorption | `t = N·1` | Expected wall-clock to a terminal outcome |
| Expected cost | `C = N·c` | The budget number that ends the "2 retries or 10?" debate |

Two structural payoffs on top: **runaway loops are mathematically impossible** (attempt
caps remove loop-back edges, so absorption is guaranteed by construction), and the
matrix is **learnable** (telemetry events recompute the probabilities as reality
changes). Where history genuinely matters (attempt 2 ≠ attempt 1), the attempt count is
encoded in the state name (`s2#1`, `s2#2`), so the model stays mathematically honest.
What Markov does *not* do: make agents smarter. It makes their behavior measurable,
bounded, and auditable.
