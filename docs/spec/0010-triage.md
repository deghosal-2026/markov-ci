# Spec 0010 — Failure triage

**Status:** Stable (v0.1 contract) · **Implements:** PRD F5

Deterministic classification happens **before any agent sees anything**. No failure
reaches an LLM unclassified; infra flakes never reach an agent at all.

## 1. Input

- JUnit XML (`--junit`), plain log text, or both.
- Tolerant parsing: malformed XML → fall back to raw-text classification with a
  warning, never a crash.

## 2. Taxonomy

| Category | Typical signatures |
|---|---|
| `lint_error` | flake8/ruff style violations, formatting drift |
| `type_mismatch` | mypy/pyright errors, `TypeError` on primitives |
| `unit_assertion` | `AssertionError`, assertion failures in JUnit |
| `infra_timeout` | `TimeoutError`, `ConnectionRefused`, spot interruption |
| `dependency_error` | registry 503, resolution failures |
| `unknown` | anything else |

## 3. Log minimizer

- Extracts the failing test block + immediate stack trace + relevant git diff.
- Hard cap: **200 lines** (property test enforces it on adversarial inputs).
- No minimizer output ever includes env values, tokens, or secret-shaped strings.

## 4. Routing

- `infra_timeout`, `dependency_error` → `a2_escalate_to_author` immediately,
  **zero tokens** — never "code-fix" an AWS spot interruption.
- `unknown` → `a2` unless the user explicitly opts in per category.
- `lint_error`, `type_mismatch`, `unit_assertion` → eligible for the agent loop
  (subject to spec 0004 policy gates).

## 5. Signature

```python
def classify(junit: Path, logs: str | None) -> TriageReport: ...
```

`TriageReport`: category, minimized context, matched signatures, routing decision.
