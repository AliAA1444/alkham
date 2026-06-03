"""Typer CLI — the thin shell over the library (command definitions only).

Each command stays thin: load config, call the library, render via ``rich``.
``AlkhamError`` becomes a clean red message + nonzero exit. CLI options use the
default-first ``typer.Option`` style for reliable short-flag parsing on Py 3.9.
"""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn, Optional

import typer
from rich.console import Console

from alkham import __version__
from alkham.backfill import backfill as run_backfill
from alkham.config import config_path, load_config, run_init_wizard
from alkham.errors import AlkhamError
from alkham.formatter import render
from alkham.moc import rebuild_project_moc
from alkham.models import RenderedNote
from alkham.parsers import get_parser_for
from alkham.sync import capture, latest_transcript, sync_latest

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="alkham",
    help="Capture AI coding-CLI sessions as readable Markdown notes.",
    add_completion=False,
)

_CLOSE_PROMPT = """\
# /close — extract durable artifacts from this session

Review our conversation and extract ONLY high-value, reusable artifacts:
- Architecture Decision Records (decision + rationale + alternatives).
- Reusable code snippets or patterns worth keeping.
- Bug postmortems (symptom -> root cause -> fix).

Skip the session entirely if it produced nothing worth keeping. alkham already
captures the full narrative, so do not summarize the whole chat.
"""


def _fail(error: Exception) -> NoReturn:
    err_console.print(f"[red]Error:[/red] {error}")
    raise typer.Exit(1)


def _report(path: Path, note: RenderedNote | None) -> None:
    if note is None:
        console.print(f"Skipped {path.name}: below the message threshold.")
        return
    console.print(f"[green]✓ Captured:[/green] {note.filename} ({note.project})")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show the alkham version and exit."
    ),
) -> None:
    """alkham — frictionless capture of AI coding sessions into Markdown."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def init() -> None:
    """Run the first-time setup wizard (pick output dir, flavor, toggles)."""
    run_init_wizard()


@app.command()
def sync(
    transcript: Optional[Path] = typer.Option(
        None, "--transcript", "-t", help="Capture a specific transcript."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Render to stdout, write nothing."
    ),
) -> None:
    """Capture the most recent session (or a specific transcript)."""
    try:
        config = load_config()
        if dry_run:
            path = transcript or latest_transcript(config)
            if path is None:
                console.print("No transcripts found — check your config sources.")
                raise typer.Exit(1)
            console.print(render(get_parser_for(path).parse(), config).markdown)
            return
        if transcript is not None:
            _report(transcript, capture(transcript, config))
            return
        result = sync_latest(config)
        if result is None:
            console.print("No transcripts found — check your config sources.")
            raise typer.Exit(1)
        _report(*result)
    except AlkhamError as error:
        _fail(error)


@app.command()
def backfill(
    since: Optional[str] = typer.Option(
        None, "--since", help="Only sessions on/after YYYY-MM-DD."
    ),
    project: Optional[str] = typer.Option(
        None, "--project", help="Only this project."
    ),
) -> None:
    """Batch-capture historical sessions across all sources."""
    try:
        config = load_config()
        notes = run_backfill(config, since=since, project=project)
    except AlkhamError as error:
        _fail(error)
    console.print(f"[green]✓[/green] Captured {len(notes)} session(s).")


@app.command(name="config")
def config_cmd(
    edit: bool = typer.Option(False, "--edit", help="Open the config in your editor."),
) -> None:
    """Print the config file path and contents (or open it)."""
    path = config_path()
    if edit:
        typer.launch(str(path))
        return
    if not path.exists():
        console.print(f"No config at {path}. Run `alkham init`.")
        raise typer.Exit(1)
    console.print(f"[bold]{path}[/bold]\n")
    console.print(path.read_text(encoding="utf-8"))


@app.command()
def moc(
    project: str = typer.Option(
        ..., "--project", help="Project to rebuild the MOC for."
    ),
) -> None:
    """Rebuild a project's Map of Content from its session notes."""
    try:
        config = load_config()
        count = rebuild_project_moc(project, config)
    except AlkhamError as error:
        _fail(error)
    console.print(f"Linked {count} note(s) into the {project} MOC.")


@app.command(name="install-close-command")
def install_close_command() -> None:
    """Install the /close artifact-extraction prompt into Claude Code."""
    target = Path.home() / ".claude" / "commands" / "close.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_CLOSE_PROMPT, encoding="utf-8")
    console.print(f"[green]✓[/green] Installed /close -> {target}")
