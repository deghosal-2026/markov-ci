"""Matrix validation (docs/spec/0002-matrix-assembly.md §1.4).

Validation never silently corrects a matrix — it reports every problem it finds so
the caller (`markov-ci validate`) can exit non-zero with the offending row/state.
A silently "fixed" matrix would make every forecast a lie.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from markov_ci.model.assemble import Chain

_TOL = 1e-9

ROW_SUM = "row_sum"
ABSORBING_IDENTITY = "absorbing_identity"
UNREACHABLE_ABSORPTION = "unreachable_absorption"


@dataclass(frozen=True, slots=True)
class Finding:
    """A single validation problem."""

    code: str
    message: str
    state: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of validating a chain."""

    ok: bool
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "findings": [
                {"code": f.code, "message": f.message, "state": f.state}
                for f in self.findings
            ],
        }


def _row_sum_findings(chain: Chain) -> list[Finding]:
    findings: list[Finding] = []
    for state_id, position in chain.index.items():
        total = float(chain.P[position].sum())
        if abs(total - 1.0) > _TOL:
            findings.append(
                Finding(
                    code=ROW_SUM,
                    message=f"row {state_id!r} sums to {total:.6f}, expected 1.0",
                    state=state_id,
                ),
            )
    return findings


def _absorbing_identity_findings(chain: Chain) -> list[Finding]:
    findings: list[Finding] = []
    for state_id in chain.absorbing:
        position = chain.index[state_id]
        row = chain.P[position]
        if abs(float(row[position]) - 1.0) > _TOL or float(row.sum()) - float(row[position]) > _TOL:
            findings.append(
                Finding(
                    code=ABSORBING_IDENTITY,
                    message=f"absorbing state {state_id!r} is not an identity row",
                    state=state_id,
                ),
            )
    return findings


def _reachable_absorption_findings(chain: Chain) -> list[Finding]:
    """Transient states that cannot reach any absorbing state."""
    positions = {state_id: chain.index[state_id] for state_id in chain.states}
    successors: dict[str, list[str]] = {state_id: [] for state_id in chain.states}
    for state_id, position in positions.items():
        for target, probability in zip(chain.states, chain.P[position], strict=True):
            if probability > _TOL:
                successors[state_id].append(target)

    # reverse reachability from the absorbing states
    can_reach: set[str] = set(chain.absorbing)
    queue: deque[str] = deque(chain.absorbing)
    while queue:
        current = queue.popleft()
        for source in chain.states:
            if current in successors[source] and source not in can_reach:
                can_reach.add(source)
                queue.append(source)

    order = {state_id: position for position, state_id in enumerate(chain.states)}
    findings = [
        Finding(
            code=UNREACHABLE_ABSORPTION,
            message=f"transient state {state_id!r} cannot reach an absorbing state",
            state=state_id,
        )
        for state_id in chain.transient
        if state_id not in can_reach
    ]
    findings.sort(key=lambda f: order[f.state] if f.state is not None else -1)
    return findings


def validate(chain: Chain) -> ValidationResult:
    """Validate a chain; return every finding (never raises on bad data)."""
    findings: list[Finding] = []
    findings.extend(_absorbing_identity_findings(chain))
    findings.extend(_row_sum_findings(chain))
    findings.extend(_reachable_absorption_findings(chain))
    return ValidationResult(ok=not findings, findings=tuple(findings))
