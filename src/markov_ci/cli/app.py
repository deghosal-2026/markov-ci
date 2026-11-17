"""The `markov-ci` command line (docs/spec/0008-cli-contract.md).

Exit codes are a stable contract: ``0`` ok · ``2`` a2 · ``3`` a3 · ``4`` invalid.
`validate` and `analyze` are implemented here; `run`, `simulate`, `queue`, and
`recompute` follow in later milestones.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from markov_ci.cli.report import build_report, render_human
from markov_ci.config import Config, ConfigCompileError, chain_from_config, load_config
from markov_ci.data import load_default_config
from markov_ci.model import validate as validate_chain

EXIT_OK = 0
EXIT_A2 = 2
EXIT_A3 = 3
EXIT_INVALID = 4

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
    except (OSError, ConfigCompileError) as exc:
        _fail(str(exc))
    except ValueError as exc:  # ConfigError is a ValueError
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
    except (OSError, ConfigCompileError) as exc:
        _fail(str(exc))
    except ValueError as exc:
        _fail(str(exc))

    report = build_report(chain, category)
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        _console.print(render_human(report))


if __name__ == "__main__":  # pragma: no cover
    app()
