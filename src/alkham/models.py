"""Shared dataclasses — Message, Session, RenderedNote.

These are the contract between layers and the **public return type of the
library API**. Keep them data-only. ``Session`` is what library consumers
receive, so its shape is a stability commitment (additive changes only after
v0.1.0). ``frozen=True`` is *shallow* — the list/dict fields stay mutable and
``Session`` is unhashable; treat them as read-only by convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    """One turn in a session."""

    role: str  # "human" | "assistant"
    content: str
    timestamp: str | None = None


@dataclass(frozen=True)
class Session:
    """A parsed AI coding-CLI session — the public return type of the library."""

    session_id: str
    source: str
    project: str
    cwd: str | None = None
    messages: list[Message] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    tools_used: dict[str, int] = field(default_factory=dict)
    started_at: str | None = None
    ended_at: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class RenderedNote:
    """A note rendered to Markdown, ready to write to disk."""

    filename: str
    markdown: str
    project: str
