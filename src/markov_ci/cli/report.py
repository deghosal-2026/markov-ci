"""Reporting helpers for the CLI (kept separate from the Typer wiring so they are
directly unit-testable and reusable by `--json`)."""

from __future__ import annotations

from typing import Any

from markov_ci.model import Chain, absorption, expected_cost, steps_to_absorb


def build_report(chain: Chain, category: str) -> dict[str, Any]:
    """Build the forecast report for a chain, from the first transient state."""
    if not chain.transient:
        raise ValueError("chain has no transient states to analyse")
    start = chain.transient[0]
    row = chain.transient.index(start)

    probabilities = absorption(chain)
    steps = steps_to_absorb(chain)
    unit_costs = dict.fromkeys(chain.transient, 1.0)
    cost = expected_cost(chain, unit_costs)

    return {
        "category": category,
        "start_state": start,
        "transient_count": len(chain.transient),
        "absorbing_count": len(chain.absorbing),
        "absorption_probabilities": {
            state_id: float(probabilities[row, column])
            for column, state_id in enumerate(chain.absorbing)
        },
        "expected_steps": float(steps[row]),
        "expected_cost": float(cost[row]),
    }


def render_human(report: dict[str, Any]) -> str:
    """Render a report as human-readable text."""
    lines = [
        f"markov-ci analyze — category={report['category']}",
        f"states: {report['transient_count']} transient · "
        f"{report['absorbing_count']} absorbing",
        "",
        f"Absorption probabilities (start: {report['start_state']})",
    ]
    for state_id, probability in report["absorption_probabilities"].items():
        lines.append(f"  {state_id:<32} {probability:.3f}")
    lines.append("")
    lines.append(f"expected steps to absorption: {report['expected_steps']:.3f}")
    lines.append(f"expected cost (unit weights):  {report['expected_cost']:.3f}")
    return "\n".join(lines)
