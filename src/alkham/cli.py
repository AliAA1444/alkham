"""Typer CLI — the thin shell over the library (command definitions only).

Phase 0 ships only ``--version``/``--help``. Real commands (``init``, ``sync``,
``backfill``, ``config``, ``moc``, ``install-close-command``) arrive in Phase 6
and stay thin: load config, call the library, render via ``rich``.
"""

from __future__ import annotations

from typing import Annotated

import typer

from alkham import __version__

app = typer.Typer(
    name="alkham",
    help="Capture AI coding-CLI sessions as readable Markdown notes.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show the alkham version and exit."),
    ] = False,
) -> None:
    """alkham — frictionless capture of AI coding sessions into Markdown."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        # No subcommand yet (Phase 6 adds them) — show help instead of erroring.
        typer.echo(ctx.get_help())
        raise typer.Exit()
