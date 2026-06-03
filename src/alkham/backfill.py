"""Batch historical capture across all enabled sources via ``parse_all``.

Expands every transcript file into its constituent sessions (so each Aider chat
in a history file is captured, not just the latest), filters by date/project,
and runs each through the same sync pipeline. Honors the message threshold.
"""

from __future__ import annotations

from alkham.config import Config
from alkham.errors import UnknownSourceError
from alkham.models import RenderedNote
from alkham.parsers import get_parser_for
from alkham.sync import find_transcripts, write_session


def backfill(
    config: Config,
    *,
    since: str | None = None,
    project: str | None = None,
) -> list[RenderedNote]:
    """Capture every matching session across all sources; returns written notes."""
    written: list[RenderedNote] = []
    for path in find_transcripts(config):
        try:
            sessions = get_parser_for(path).parse_all()
        except UnknownSourceError:
            continue
        for session in sessions:
            if since and (session.started_at or "")[:10] < since:
                continue
            if project and session.project != project:
                continue
            note = write_session(session, config)
            if note is not None:
                written.append(note)
    return written
