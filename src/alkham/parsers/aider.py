"""Aider history parser — THE MOAT (Phase 4).

Aider writes a single **append-only** ``.aider.chat.history.md`` per project,
holding *many* sessions. This parser splits it on the ``# aider chat started
at`` markers: ``parse_all()`` returns one ``Session`` per delimited chat (with
a stable per-session id, so re-syncs are idempotent and newly appended
sessions become new notes), and ``parse()`` returns the most-recent chat (what
``sync`` captures).

Aider history is Markdown, not JSONL, and carries less structured metadata than
Claude Code — tool/file breadcrumbs are left empty rather than faked. Within a
chat, user prompts are ``####`` (h4) blocks and the assistant reply is the text
between them; Aider's ``>`` input-echo lines are ignored.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from alkham.models import Message, Session
from alkham.parsers.base import register

_HISTORY_FILENAME = ".aider.chat.history.md"
_MARKER = "aider chat started at"
_SESSION_HEADER = re.compile(r"^# aider chat started at (.+?)\s*$", re.MULTILINE)


def _session_id(path: Path, timestamp: str, ordinal: int) -> str:
    """Stable per-session id: same input -> same id (idempotent re-sync)."""
    raw = f"{path}|{timestamp}|{ordinal}"
    return "aider-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _is_user_line(line: str) -> bool:
    """True for an Aider user-prompt line (``#### ...``) but not ``#####`` h5."""
    return line.startswith("#### ") or line.rstrip() == "####"


def _parse_turns(body: str) -> list[Message]:
    lines = body.splitlines()
    messages: list[Message] = []
    i, n = 0, len(lines)
    while i < n:
        if _is_user_line(lines[i]):
            human: list[str] = []
            while i < n and _is_user_line(lines[i]):
                human.append(lines[i][4:].strip())
                i += 1
            content = "\n".join(h for h in human if h).strip()
            if content:
                messages.append(Message("human", content, None))
        else:
            reply: list[str] = []
            while i < n and not _is_user_line(lines[i]):
                if not lines[i].lstrip().startswith(">"):
                    reply.append(lines[i])
                i += 1
            text = "\n".join(reply).strip()
            if text:
                messages.append(Message("assistant", text, None))
    return messages


class AiderParser:
    """Splits Aider's append-only history into one Session per chat."""

    source_name = "aider"

    def can_parse(self, path: Path) -> bool:
        if path.name == _HISTORY_FILENAME:
            return True
        if path.suffix.lower() != ".md":
            return False
        try:
            with path.open(encoding="utf-8") as f:
                head = f.read(4096)
        except OSError:
            return False
        return _MARKER in head

    def parse_all(self, path: Path) -> list[Session]:
        text = path.read_text(encoding="utf-8")
        project = path.parent.name
        cwd = str(path.parent)
        matches = list(_SESSION_HEADER.finditer(text))
        sessions: list[Session] = []
        for ordinal, match in enumerate(matches):
            timestamp = str(match.group(1)).strip()
            start = match.end()
            if ordinal + 1 < len(matches):
                end = matches[ordinal + 1].start()
            else:
                end = len(text)
            sessions.append(
                Session(
                    session_id=_session_id(path, timestamp, ordinal),
                    source=self.source_name,
                    project=project,
                    cwd=cwd,
                    messages=_parse_turns(text[start:end]),
                    started_at=timestamp,
                )
            )
        return sessions

    def parse(self, path: Path) -> Session:
        sessions = self.parse_all(path)
        if sessions:
            return sessions[-1]
        # No recognizable session header — return an empty session, don't crash.
        return Session(
            session_id=_session_id(path, "", 0),
            source=self.source_name,
            project=path.parent.name,
            cwd=str(path.parent),
        )


register(AiderParser())
