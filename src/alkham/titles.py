"""Pure title / slug / filename derivation with noise-skipping.

The filename is ``<date>_<slug>_<id6>.md`` — a date prefix, a slug from the
first *substantive* human message (skipping slash-commands like ``/clear``),
and a stable 6-char id slice for collision resistance. Pure — no I/O.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from alkham.models import Message, Session

_NOISE = re.compile(r"^/[a-z][\w-]*(\s|$)")
_SLUG_DROP = re.compile(r"[^\w\s-]")
_SLUG_SPACE = re.compile(r"[\s_]+")
_SLUG_DASH = re.compile(r"-+")


def is_noise(text: str) -> bool:
    """True for empty messages and slash-commands (``/clear``, ``/model`` …)."""
    stripped = text.strip()
    return not stripped or bool(_NOISE.match(stripped))


def slugify(text: str) -> str:
    """Lowercase, hyphenated, punctuation-free slug; ``untitled`` if empty."""
    slug = _SLUG_DROP.sub("", text.strip().lower())
    slug = _SLUG_SPACE.sub("-", slug)
    slug = _SLUG_DASH.sub("-", slug).strip("-")
    return slug[:60] or "untitled"


def make_filename(session: Session) -> str:
    """Build the collision-resistant note filename for a session."""
    date = _date_prefix(session.started_at)
    slug = _title_slug(session.messages)
    sid = _id_slice(session.session_id)
    return f"{date}_{slug}_{sid}.md"


def _title_slug(messages: Iterable[Message]) -> str:
    for message in messages:
        if message.role == "human" and not is_noise(message.content):
            return slugify(message.content)
    return "untitled"


def _date_prefix(timestamp: str | None) -> str:
    return timestamp[:10] if timestamp and len(timestamp) >= 10 else "undated"


def _id_slice(session_id: str) -> str:
    return hashlib.sha1(session_id.encode("utf-8")).hexdigest()[:6]
