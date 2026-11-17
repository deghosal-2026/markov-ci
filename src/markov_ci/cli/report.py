"""Reporting helpers for the CLI (kept separate from the Typer wiring so they are
directly unit-testable and reusable by `--json`)."""

from __future__ import annotations

from typing import Any

from markov_ci.model import Chain, absorption, expected_cost, steps_to_absorb
from markov_ci.queueing import (
    erlang_c,
    exponential_services,
    poisson_arrivals,
    simulate,
)


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


def build_queue_report(
    *,
    lam: float,
    mu: float,
    c: int,
    human_share: float = 0.6,
    simulate_pools: bool = False,
    seed: int = 0,
    duration: float = 1000.0,
) -> dict[str, Any]:
    """Size the human and agent runner pools side by side."""
    if not 0.0 < human_share < 1.0:
        raise ValueError("human_share must be strictly between 0 and 1")
    human_c = max(1, round(c * human_share))
    agent_c = c - human_c
    if agent_c < 1:
        raise ValueError(f"c={c} is too small for a human_share of {human_share}")

    human_lam = lam * human_share
    agent_lam = lam - human_lam

    def _pool(pool_lam: float, pool_c: int, offset: int) -> dict[str, Any]:
        metrics = erlang_c(lam=pool_lam, mu=mu, c=pool_c)
        entry: dict[str, Any] = {
            "lambda": pool_lam,
            "c": pool_c,
            "rho": metrics.rho,
            "p_wait": metrics.p_wait,
            "mean_wait": metrics.mean_wait,
            "p95_wait": metrics.p95_wait,
        }
        if simulate_pools:
            arrivals = poisson_arrivals(lam=pool_lam, duration=duration, seed=seed + offset)
            services = exponential_services(mu=mu, n=len(arrivals), seed=seed + offset + 100)
            sim = simulate(arrivals, services, c=pool_c)
            entry["simulation"] = {
                "p50_wait": sim.p50_wait,
                "p95_wait": sim.p95_wait,
                "p99_wait": sim.p99_wait,
                "mean_wait": sim.mean_wait,
                "p_wait": sim.p_wait,
            }
        return entry

    return {
        "mu": mu,
        "c": c,
        "human_share": human_share,
        "pools": {
            "human": _pool(human_lam, human_c, 0),
            "agent": _pool(agent_lam, agent_c, 1),
        },
    }


def render_queue(report: dict[str, Any]) -> str:
    """Render a queue report as human-readable text."""
    lines = [
        f"markov-ci queue — mu={report['mu']} · c={report['c']} "
        f"· human_share={report['human_share']}",
        "",
    ]
    for name in ("human", "agent"):
        pool = report["pools"][name]
        lines.append(
            f"[{name}] c={pool['c']} lambda={pool['lambda']:.1f} "
            f"rho={pool['rho']:.3f}",
        )
        lines.append(
            f"    p_wait={pool['p_wait']:.3f} mean_wait={pool['mean_wait']:.4f} "
            f"p95_wait={pool['p95_wait']:.4f}",
        )
        if "simulation" in pool:
            sim = pool["simulation"]
            lines.append(
                f"    sim: p50={sim['p50_wait']:.4f} p95={sim['p95_wait']:.4f} "
                f"p99={sim['p99_wait']:.4f}",
            )
    return "\n".join(lines)


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
