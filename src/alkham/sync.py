"""Orchestrator — find a transcript, parse, route, format, write, link MOC.

Pure decisions live in routing/titles/formatter; this module composes them and
performs the file writes (the impure edge). ``write_session`` honors the
``min_messages`` threshold — returning ``None`` so the caller can report the
skip rather than writing noise.
"""

from __future__ import annotations

from pathlib import Path

from alkham.config import Config
from alkham.formatter import render
from alkham.moc import ensure_linked
from alkham.models import RenderedNote, Session
from alkham.parsers import get_parser_for
from alkham.parsers.base import discoverers
from alkham.routing import resolve_output_dir


def find_transcripts(config: Config) -> list[Path]:
    """All transcript files across enabled sources (parser-driven discovery)."""
    paths: list[Path] = []
    for source_name, discover in discoverers().items():
        if source_name in config.sources:
            paths.extend(discover(config))
    return paths


def latest_transcript(config: Config) -> Path | None:
    """The most recently modified transcript across enabled sources."""
    paths = find_transcripts(config)
    if not paths:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime)


def write_session(session: Session, config: Config) -> RenderedNote | None:
    """Render + write a session, honoring the threshold. ``None`` = skipped."""
    if len(session.messages) < config.min_messages:
        return None
    note = render(session, config)
    out_path = resolve_output_dir(session, config) / note.filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(note.markdown, encoding="utf-8")
    ensure_linked(note, config)
    return note


def capture(path: Path, config: Config) -> RenderedNote | None:
    """Parse a specific transcript (most-recent session) and write it."""
    return write_session(get_parser_for(path).parse(), config)


def sync_latest(config: Config) -> tuple[Path, RenderedNote | None] | None:
    """Find and capture the most recent session. ``None`` = nothing found."""
    path = latest_transcript(config)
    if path is None:
        return None
    return path, capture(path, config)
