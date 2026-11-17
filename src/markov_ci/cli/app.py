"""The `markov-ci` command line (docs/spec/0008-cli-contract.md).

Exit codes are a stable contract: ``0`` ok · ``2`` a2 · ``3`` a3 · ``4`` invalid.
`validate`, `analyze`, and `run` are implemented here; `simulate`, `queue`, and
`recompute` follow in later milestones.
"""

from __future__ import annotations

import json
import shlex
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
from rich.console import Console

from markov_ci.agents import HarnessAgent, HarnessError, HarnessSpec, HarnessTimeout, SimulatedAgent
from markov_ci.cli.report import build_queue_report, build_report, render_human, render_queue
from markov_ci.config import (
    Config,
    ConfigCompileError,
    chain_from_config,
    load_config,
    success_curve,
)
from markov_ci.data import load_default_config
from markov_ci.engine import A1, A2, A3, LoopConfig, Sandbox, run_loop
from markov_ci.guardrails import patch_branch
from markov_ci.model import monte_carlo
from markov_ci.model import validate as validate_chain
from markov_ci.telemetry import JsonlSink
from markov_ci.triage import classify, minimize, parse_junit

EXIT_OK = 0
EXIT_A2 = 2
EXIT_A3 = 3
EXIT_INVALID = 4

_EXIT_CODES = {A1: EXIT_OK, A2: EXIT_A2, A3: EXIT_A3}

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Markov-governed, self-healing CI/CD.",
)

_console = Console(soft_wrap=True)


def _resolve_config(config: Path | None) -> Config:
    if config is None:
        return load_default_config()
    return load_config(config)


def _fail(message: str) -> None:
    _console.print(f"[red]invalid config:[/red] {message}")
    raise typer.Exit(code=EXIT_INVALID)


@app.command()
def validate(
    config: Annotated[Path | None, typer.Argument(help="config YAML (default: packaged)")] = None,
) -> None:
    """Validate a config and print a summary of the assembled matrix."""
    try:
        resolved = _resolve_config(config)
        chain = chain_from_config(resolved, category="default")
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    result = validate_chain(chain)
    if not result.ok:
        for finding in result.findings:
            _console.print(f"[red]{finding.code}[/red]: {finding.message}")
        raise typer.Exit(code=EXIT_INVALID)

    _console.print(
        f"ok: {len(chain.transient)} transient · {len(chain.absorbing)} absorbing "
        f"· {len(chain.states)} states",
    )


@app.command()
def analyze(
    config: Annotated[Path | None, typer.Argument(help="config YAML (default: packaged)")] = None,
    category: Annotated[str, typer.Option("--category", "-c")] = "default",
    json_output: Annotated[bool, typer.Option("--json", help="machine-readable output")] = False,
) -> None:
    """Print N, B, t, C for a failure category."""
    try:
        resolved = _resolve_config(config)
        chain = chain_from_config(resolved, category=category)
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    report = build_report(chain, category)
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        _console.print(render_human(report))


def _build_adapter(config: Config, category: str, seed: int):  # type: ignore[no-untyped-def]
    if config.agent.adapter == "harness":
        if config.agent.harness is None:
            _fail("agent.adapter is 'harness' but no harness block is configured")
        assert config.agent.harness is not None
        return HarnessAgent(
            HarnessSpec(
                command_template=config.agent.harness.command_template,
                timeout_seconds=config.agent.harness.timeout_seconds,
            ),
        )
    return SimulatedAgent(success_curve(config, "default", category), seed=seed)


@app.command()
def run(  # noqa: PLR0913
    config: Path | None = typer.Argument(None, help="config YAML (default: packaged)"),
    junit: Path = typer.Option(..., "--junit", help="JUnit XML report"),
    seed: int = typer.Option(0, "--seed", help="deterministic RNG seed"),
    repo: Path = typer.Option(Path("."), "--repo", help="repository to sandbox"),
    pr_number: int | None = typer.Option(None, "--pr-number"),
    failing_command: str = typer.Option("pytest -q", "--failing-command"),
    regression_command: str | None = typer.Option(None, "--regression-command"),
    json_output: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Run the governed remediation loop and exit on the absorbing state."""
    try:
        resolved = _resolve_config(config)
        junit_text = Path(junit).read_text(encoding="utf-8")
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    report = parse_junit(junit_text)
    triage = classify(report.failures, logs=junit_text)
    if not triage.eligible:
        _console.print(
            f"[yellow]{triage.category.value}[/yellow]: {triage.reason} — escalating (a2)",
        )
        raise typer.Exit(code=EXIT_A2)

    category = triage.category.value
    run_id = uuid4().hex
    branch = (
        patch_branch(pr_number=pr_number) if pr_number is not None
        else patch_branch(run_id=run_id)
    )
    loop_config = LoopConfig(
        policy=resolved.policy.to_policy(),
        success_curve=success_curve(resolved, "default", category),
        allow_write=tuple(resolved.agent.allow_write),
        deny_write=tuple(resolved.agent.deny_write),
        failing_command=tuple(shlex.split(failing_command)),
        regression_command=tuple(shlex.split(regression_command or failing_command)),
    )

    sink = None
    events_path: str | None = None
    if resolved.telemetry.sink == "file":
        sink = JsonlSink(resolved.telemetry.path)
        events_path = resolved.telemetry.path

    sandbox = Sandbox(repo)
    context = minimize(list(report.failures)).text
    try:
        result = run_loop(
            adapter=_build_adapter(resolved, category, seed),
            category=triage.category,
            context=context,
            config=loop_config,
            sandbox=sandbox,
            run_id=run_id,
            pr_number=pr_number,
            sink=sink,
            patch_branch=branch.name,
        )
    except HarnessTimeout as exc:
        _console.print(f"[red]harness timeout:[/red] {exc}")
        raise typer.Exit(code=EXIT_A3) from exc
    except HarnessError as exc:
        _console.print(f"[red]harness error:[/red] {exc}")
        raise typer.Exit(code=EXIT_A2) from exc
    finally:
        sandbox.close()
        if sink is not None:
            sink.close()

    if events_path is not None:
        result = replace(result, events_path=events_path)

    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        _console.print(
            f"absorbed: {result.absorbing_state} · tokens {result.tokens_used} · "
            f"{result.wall_clock_ms} ms · branch {result.patch_branch}",
        )
    raise typer.Exit(code=_EXIT_CODES.get(result.absorbing_state or A2, EXIT_A2))


@app.command()
def simulate(
    config: Path | None = typer.Argument(None, help="config YAML (default: packaged)"),
    category: str = typer.Option("default", "--category", "-c"),
    runs: int = typer.Option(10_000, "--runs"),
    seed: int = typer.Option(0, "--seed"),
    json_output: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Monte-Carlo cross-check of the analytic forecast."""
    try:
        resolved = _resolve_config(config)
        chain = chain_from_config(resolved, category=category)
        result = monte_carlo(chain, runs=runs, seed=seed)
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    payload = {
        "category": category,
        "runs": result.runs,
        "absorption_probabilities": dict(result.absorption),
        "mean_steps": result.mean_steps,
        "steps_ci": list(result.steps_ci),
        "mean_cost": result.mean_cost,
        "cost_ci": list(result.cost_ci),
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _console.print(
            f"simulate — category={category} · runs={result.runs}",
        )
        for state_id, probability in sorted(result.absorption.items()):
            _console.print(f"  {state_id:<32} {probability:.3f}", markup=False)
        _console.print(
            f"mean steps: {result.mean_steps:.3f} "
            f"(95% CI {result.steps_ci[0]:.3f}–{result.steps_ci[1]:.3f})",
        )


@app.command()
def queue(  # noqa: PLR0913
    lam: float = typer.Option(..., "--lambda", "--lam", help="arrival rate (per hour)"),
    mu: float = typer.Option(..., "--mu", help="per-runner service rate (per hour)"),
    c: int = typer.Option(..., "--c", help="total runners"),
    human_share: float = typer.Option(0.6, "--human-share"),
    simulate_pools: bool = typer.Option(False, "--simulate", help="run the burst simulator"),
    json_output: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Size the human and agent runner pools side by side."""
    try:
        report = build_queue_report(
            lam=lam, mu=mu, c=c, human_share=human_share, simulate_pools=simulate_pools,
        )
    except ValueError as exc:
        _fail(str(exc))

    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        _console.print(render_queue(report), markup=False)


if __name__ == "__main__":  # pragma: no cover
    app()
