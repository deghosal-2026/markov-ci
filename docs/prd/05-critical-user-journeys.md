# 05 — Critical User Journeys (CUJs)

Six journeys cover the product's value. Each has entry conditions, steps, measurable
success criteria, and feature traceability (appendix 12 has the full matrix).
If a journey fails, the release blocks.

---

## CUJ-1 — Priya forecasts and approves agent rollout
*Persona: platform engineer · Primary value: O1*

**Entry conditions:** Org wants agents in CI; Priya owns the budget; nothing installed.

**Steps**
1. `pip install markov-ci` → zero-config sanity check: `markov-ci analyze` prints the
   worked example with golden numbers (F11).
2. Adapts the default YAML to her pipeline; `markov-ci validate config.yaml` → prints the
   assembled matrix summary (F1, F2).
3. `markov-ci analyze --category unit_assertion --json` → expected attempts, tokens,
   absorption probabilities, per-attempt decay (F3).
4. Tunes `policy:` budgets until forecast spend fits her envelope (F4).
5. `markov-ci simulate --runs 10000` → cross-checks the analytic forecast (F17).
6. Pins the config in the platform repo; CI adopts it.

**Success criteria:** forecast produced in < 10 minutes from install; every number
traceable to config; she defends the budget line in one review meeting.
**Failure handling:** no telemetry yet → illustrative priors, labeled `source: prior`;
invalid matrix → exit 4 with the exact offending row.

---

## CUJ-2 — Marcus gets a trivial failure fixed without context-switching
*Persona: developer · Primary value: the "self-healing" promise — realized when a
validated patch is delivered, not when a loop merely runs*

**Entry conditions:** Marcus pushes a PR with a lint/unit failure; governance is wired in.

**Steps**
1. `s0` fails → deterministic triage classifies `lint_error` and minimizes the log (F5).
2. Agent loop: patch proposed → validated in isolation → regression checked (F6, F8).
3. Patch lands on `ai-fix/pr-42`; a PR comment posts diff + telemetry summary (F7, F8).
4. Marcus reviews the one-paragraph summary and the small diff; merges it into his PR.

**Success criteria:** first-time-to-green < 3 minutes; Marcus never leaves his editor
unless the patch needs real review; the event stream shows the full path.
**Failure handling:** decayed confidence or a guardrail trip → `a2` with diagnostic
notes — Marcus fixes it himself, zero mystery.

---

## CUJ-3 — Priya sleeps through 20 simultaneous agent loops
*Persona: platform engineer · Primary value: O2*

**Entry conditions:** Tuesday 2 PM; twenty agent repair loops fire concurrently.

**Steps**
1. Each loop runs under policy: token + wall-clock budgets, attempt caps (F4).
2. Any runaway tendency absorbs into `a3_budget_exceeded` — by construction (F2, F8).
3. Every hop emits a JSONL event (F9).
4. Agent traffic rides the low-priority pool; human builds keep the warm pool —
   `markov-ci queue` sized both (F16).

**Success criteria:** bounded worst-case spend (computable in advance); human queue p95
stays < 60 s; an audit trail exists for every run.
**Failure handling:** budgets trip mid-attempt → clean `a3` absorption + event, never
a kill -9 with no evidence.

---

## CUJ-4 — Sam plugs his harness into governance in an afternoon
*Persona: agent builder · Primary value: ecosystem fit (F19, F6)*

**Entry conditions:** Sam already runs Claude Code/OpenCode/Aider headless in CI;
no governance around it.

**Steps**
1. Implements the one-method `AgentAdapter` protocol — or just fills the
   `agent.harness.command_template` (F6, F19).
2. Runs the offline conformance suite against simulated fixtures (F13).
3. First governed runs emit `adapter: claude-code` on every event (F9).
4. A week later, `recompute events.jsonl` produces his harness's real matrix (F21).

**Success criteria:** conformance suite green in one afternoon; no SDK added to core;
per-harness priors emerge from his own telemetry.
**Failure handling:** harness CLI churn → BYO-command adapter + community templates
absorb it (F28).

---

## CUJ-5 — Dana approves spend with one page, then audits it
*Persona: engineering leader · Primary value: FinOps credibility*

**Entry conditions:** Dana asks "what will agents cost, and did it hold?"

**Steps**
1. Priya runs `markov-ci analyze --json` → one-page forecast (F3, F10).
2. Dana approves the rollout.
3. Weeks later: actual telemetry events → `recompute` → actual matrix vs forecast
   within 10% (F9, F21, F17).

**Success criteria:** forecast vs actual within 10%; every deviation explainable
(category mix shift, harness change); audit trail complete.
**Failure handling:** divergence beyond CI → drift flagged, priors updated — the
system says so itself rather than hiding it.

---

## CUJ-6 — Marcus trusts that green means green
*Persona: developer · Primary value: O4, test-suite integrity*

**Entry conditions:** an agent proposes a patch that touches a test file.

**Steps**
1. Guardrails evaluate the diff: path allowlist, then TMR check (F7).
2. Assertion deletion or test-heavy diff → hard stop to `a2` + `mandatory_review` flag.
3. The PR comment explicitly names what the agent tried to change.

**Success criteria:** zero weakened assertions reach review unnoticed; every flagged
patch requires a human decision; adversarial fixtures all blocked in tests.
**Failure handling:** false positives (legit test updates) → reviewer sees the ratio
and the diff and can accept deliberately — friction only where it belongs.

---

## CUJ blocking rule

Every MUST feature (06) traces to at least one CUJ; every CUJ step traces to at least
one shipped feature or an explicit v0.2 marker. The e2e demo suite (F13, F14) executes
CUJ-2, CUJ-3, and CUJ-6 paths on every PR — the journeys are tests, not prose.
