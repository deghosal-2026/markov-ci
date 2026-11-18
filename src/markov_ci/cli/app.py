"""The `markov-ci` command line (docs/spec/0008-cli-contract.md).

Exit codes are a stable contract: ``0`` a1 · ``1`` a2 · ``2`` usage · ``3`` a3 ·
``4`` invalid · ``5`` internal (ADR-0017).
`validate`, `analyze`, and `run` are implemented here; `simulate`, `queue`, and
`recompute` follow in later milestones.
"""

from __future__ import annotations

import hashlib
import json
import shlex
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
import yaml
from rich.console import Console

from markov_ci import __version__
from markov_ci.agents import HarnessAgent, HarnessError, HarnessSpec, SimulatedAgent
from markov_ci.agents.templates import TEMPLATES, template_spec
from markov_ci.cli.report import build_queue_report, build_report, render_human, render_queue
from markov_ci.config import (
    Config,
    ConfigCompileError,
    chain_from_config,
    confidence_gate_warnings,
    load_config,
    success_curve,
)
from markov_ci.data import load_default_config
from markov_ci.engine import A1, A2, A3, LoopConfig, WorktreeValidator, run_loop
from markov_ci.guardrails import parse_diff_paths, patch_branch, publish_patch
from markov_ci.model import monte_carlo
from markov_ci.model import validate as validate_chain
from markov_ci.telemetry import JsonlSink, TransitionEvent, utc_now
from markov_ci.telemetry import recompute as recompute_priors
from markov_ci.triage import classify, minimize, parse_junit

EXIT_OK = 0
EXIT_A2 = 1
EXIT_A3 = 3
EXIT_INVALID = 4
EXIT_INTERNAL = 5

_EXIT_CODES = {A1: EXIT_OK, A2: EXIT_A2, A3: EXIT_A3}

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Markov-planned, guardrailed CI/CD.",
)

_console = Console(soft_wrap=True)


def _resolve_config(config: Path | None) -> Config:
    if config is None:
        return load_default_config()
    return load_config(config)


def _fail(message: str) -> None:
    _console.print(f"[red]invalid config:[/red] {message}")
    raise typer.Exit(code=EXIT_INVALID)


def _emit_terminal(
    sink: JsonlSink | None,
    *,
    run_id: str,
    pr_number: int | None,
    to_state: str,
    category: str,
    adapter_id: str,
) -> None:
    """Emit the terminal transition for an exit outside the loop (M13.22)."""
    if sink is None:
        return
    sink.emit(
        TransitionEvent(
            event="transition",
            run_id=run_id,
            commit_sha="",
            pr_number=pr_number,
            from_state="s1_failure_triage",
            to_state=to_state,
            duration_ms=0,
            tokens_used=None,
            failure_category=category,
            attempt=1,
            adapter=adapter_id,
            ts=utc_now(),
        ),
    )


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
    start: Annotated[
        str | None,
        typer.Option("--start", help="start state (default: s1 — failed builds)"),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="machine-readable output")] = False,
) -> None:
    """Print N, B, t, C for a failure category."""
    try:
        resolved = _resolve_config(config)
        chain = chain_from_config(resolved, category=category)
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    try:
        report = build_report(chain, category, start=start)
    except ValueError as exc:
        _fail(str(exc))
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        _console.print(render_human(report))
        for warning in confidence_gate_warnings(resolved, category=category):
            _console.print(f"[yellow]warning:[/yellow] {warning}")


def _build_adapter(  # type: ignore[no-untyped-def]
    config: Config, category: str, seed: int, *,
    adapter: str | None = None, repo: Path | None = None,
):
    selected = adapter or config.agent.adapter
    if selected in TEMPLATES:
        # a named template (M13.31): wire the shipped T2 invocation pattern
        return HarnessAgent(
            template_spec(selected), cwd=repo, env_allow=tuple(config.agent.env),
        )
    if selected == "harness":
        if config.agent.harness is None:
            _fail("agent.adapter is 'harness' but no harness block is configured")
        assert config.agent.harness is not None
        return HarnessAgent(
            HarnessSpec(
                command_template=config.agent.harness.command_template,
                timeout_seconds=config.agent.harness.timeout_seconds,
                id=config.agent.harness.name or "harness",
            ),
            cwd=repo,
            env_allow=tuple(config.agent.env),
        )
    if selected != "simulated":
        _fail(f"unsupported adapter: {selected!r} (use 'simulated' or 'harness')")
    return SimulatedAgent(success_curve(config, "default", category), seed=seed)


@app.command()
def run(  # noqa: PLR0913
    config: Path | None = typer.Argument(None, help="config YAML (default: packaged)"),
    junit: Path = typer.Option(..., "--junit", help="JUnit XML report"),
    seed: int = typer.Option(0, "--seed", help="deterministic RNG seed"),
    repo: Path = typer.Option(Path("."), "--repo", help="repository to validate"),
    pr_number: int | None = typer.Option(None, "--pr-number"),
    failing_command: str | None = typer.Option(
        None, "--failing-command", help="command that reproduces the failure",
    ),
    regression_command: str | None = typer.Option(
        None, "--regression-command",
        help="broader regression command; omit to skip s4",
    ),
    max_tokens: int | None = typer.Option(
        None, "--max-tokens", help="override policy.max_tokens for this run",
    ),
    wall_clock: int | None = typer.Option(
        None, "--wall-clock", help="override policy.wall_clock_seconds for this run",
    ),
    adapter: str | None = typer.Option(
        None, "--adapter", help="override agent.adapter (simulated|harness)",
    ),
    container_image: str | None = typer.Option(
        None, "--container-image",
        help="run validation in this container image (ADR-0012)",
    ),
    output_patch: Path | None = typer.Option(
        None, "--output-patch", help="write the validated patch to this file",
    ),
    publish: bool = typer.Option(
        False, "--publish",
        help="apply and push the validated diff to a fresh ai-fix/* branch",
    ),
    json_output: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Run the governed remediation loop and exit on the absorbing state."""
    try:
        resolved = _resolve_config(config)
        junit_text = Path(junit).read_text(encoding="utf-8")
    except (OSError, ConfigCompileError, ValueError) as exc:
        _fail(str(exc))

    report = parse_junit(junit_text)
    run_id = uuid4().hex
    sink = None
    events_path: str | None = None
    if resolved.telemetry.sink == "file":
        sink = JsonlSink(resolved.telemetry.path)
        events_path = resolved.telemetry.path

    adapter_id = adapter or resolved.agent.adapter
    validator = WorktreeValidator(
        repo, container_image=container_image or resolved.agent.container,
    )
    try:
        triage = classify(report.failures, logs=junit_text)
        if not triage.eligible:
            _emit_terminal(
                sink, run_id=run_id, pr_number=pr_number, to_state=A2,
                category=triage.category.value, adapter_id=adapter_id,
            )
            _console.print(
                f"[yellow]{triage.category.value}[/yellow]: {triage.reason} "
                "— escalating (a2)",
            )
            raise typer.Exit(code=EXIT_A2)

        category = triage.category.value
        branch = (
            patch_branch(pr_number=pr_number) if pr_number is not None
            else patch_branch(run_id=run_id)
        )
        try:
            policy = resolved.policy.to_policy()
            if max_tokens is not None:
                policy = replace(policy, max_tokens=max_tokens)
            if wall_clock is not None:
                policy = replace(policy, wall_clock_seconds=wall_clock)
            loop_config = LoopConfig(
                policy=policy,
                success_curve=success_curve(resolved, "default", category),
                allow_write=tuple(resolved.agent.allow_write),
                deny_write=tuple(resolved.agent.deny_write),
                failing_command=tuple(
                    shlex.split(
                        failing_command or resolved.agent.failing_command or "pytest -q",
                    ),
                ),
                regression_command=tuple(
                    shlex.split(regression_command or resolved.agent.regression_command)
                    if (regression_command or resolved.agent.regression_command)
                    else (),
                ),
                env_allow=tuple(resolved.agent.env),
            )
            context = minimize(list(report.failures)).text
            config_hash = hashlib.sha256(
                json.dumps(resolved.model_dump(mode="json"), sort_keys=True).encode(),
            ).hexdigest()[:12]
        except (ConfigCompileError, ValueError) as exc:
            # a compile-time problem (e.g. no prior for the category) is invalid
            # config (exit 4), not an internal failure (M14 finding).
            _fail(str(exc))
        try:
            result = run_loop(
                adapter=_build_adapter(
                    resolved, category, seed, adapter=adapter, repo=repo,
                ),
                category=triage.category,
                context=context,
                config=loop_config,
                validator=validator,
                run_id=run_id,
                pr_number=pr_number,
                sink=sink,
                patch_branch=branch.name,
                config_hash=config_hash,
                model_version=__version__,
            )
        except HarnessError as exc:
            # a terminal event so the stream and the exit code agree (M13.22).
            _emit_terminal(
                sink, run_id=run_id, pr_number=pr_number, to_state=A2,
                category=category, adapter_id=adapter_id,
            )
            _console.print(f"[red]harness error:[/red] {exc}")
            raise typer.Exit(code=EXIT_A2) from exc
        except typer.Exit:
            raise
        except Exception:
            # an internal/infra failure: documented code 5 + a terminal event (M13.37)
            _emit_terminal(
                sink, run_id=run_id, pr_number=pr_number, to_state=A2,
                category=category, adapter_id=adapter_id,
            )
            _console.print("[red]internal error:[/red] see the event stream")
            raise typer.Exit(code=EXIT_INTERNAL) from None
    finally:
        validator.close()
        if sink is not None:
            sink.close()

    if events_path is not None:
        result = replace(result, events_path=events_path)

    if publish:
        # report patch_branch only after a successful push, else null (M13.24)
        published = None
        if result.absorbing_state == A1 and result.patch:
            published = publish_patch(
                repo,
                branch=branch.name,
                diff=result.patch,
                paths=tuple(parse_diff_paths(result.patch)),
            )
        result = replace(result, patch_branch=published)

    if output_patch is not None and result.patch:
        Path(output_patch).write_text(result.patch, encoding="utf-8")
        result = replace(result, patch_path=str(output_patch))

    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        _console.print(
            f"absorbed: {result.absorbing_state} · tokens "
            f"{result.tokens_used if result.tokens_used is not None else 'n/a'} · "
            f"{result.wall_clock_ms} ms · branch {result.patch_branch}",
        )
        if result.mandatory_review:
            _console.print(
                "[red]mandatory review:[/red] test-weakening guardrail tripped — "
                f"{'; '.join(result.guardrail_report)}",
            )
    raise typer.Exit(code=_EXIT_CODES.get(result.absorbing_state or A2, EXIT_A2))


@app.command()
def recompute(
    events: Path = typer.Argument(..., help="events.jsonl from a run"),
    config: Path | None = typer.Option(None, "--config", help="config for priors/alpha"),
    alpha: float = typer.Option(1.0, "--alpha", help="prior pseudo-count strength"),
    include_synthetic: bool = typer.Option(
        False, "--include-synthetic", help="include offline simulated events",
    ),
    json_output: bool = typer.Option(False, "--json", help="machine-readable output"),
) -> None:
    """Rebuild empirical priors from a telemetry event stream."""
    try:
        lines = Path(events).read_text(encoding="utf-8").splitlines()
        parsed = [json.loads(line) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        _fail(str(exc))

    prior = None
    if config is not None:
        try:
            resolved = load_config(config)
        except (OSError, ConfigCompileError, ValueError) as exc:
            _fail(str(exc))
        prior = {
            adapter: {category: block.success for category, block in categories.items()}
            for adapter, categories in resolved.priors.items()
        }

    priors = recompute_priors(
        parsed, alpha=alpha, prior=prior, include_synthetic=include_synthetic,
    )
    if json_output:
        typer.echo(json.dumps(priors, indent=2, sort_keys=True))
    else:
        typer.echo(yaml.safe_dump(priors, sort_keys=True))


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
