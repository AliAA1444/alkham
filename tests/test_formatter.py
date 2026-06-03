"""Phase 5 — formatter rendering, toggles, and injection defenses."""

from __future__ import annotations

from typing import Any

import yaml

from alkham.config import Config, FeatureFlags, OutputConfig
from alkham.formatter import render
from alkham.models import Message, Session


def _session(messages: list[Message]) -> Session:
    return Session(
        session_id="abc123",
        source="claude-code",
        project="crowdflow",
        started_at="2026-05-14T10:00:00Z",
        messages=messages,
    )


def _config(**features: bool) -> Config:
    return Config(
        output=OutputConfig(flavor="obsidian", base_path="/v"),
        features=FeatureFlags(**features),
    )


def _parse_frontmatter(markdown: str) -> dict[str, Any]:
    assert markdown.startswith("---\n")
    end = markdown.index("\n---\n", 4)
    return yaml.safe_load(markdown[4:end])


def test_renders_conversation_turns() -> None:
    msgs = [Message("human", "Hi"), Message("assistant", "Hello")]
    note = render(_session(msgs), _config())
    assert "👤" in note.markdown and "🤖" in note.markdown
    assert "Hi" in note.markdown and "Hello" in note.markdown
    assert note.filename.endswith(".md")
    assert note.project == "crowdflow"


def test_frontmatter_toggle_on() -> None:
    note = render(_session([Message("human", "Add auth")]), _config(frontmatter=True))
    fm = _parse_frontmatter(note.markdown)
    assert fm["source"] == "claude-code"
    assert fm["project"] == "crowdflow"
    assert fm["date"] == "2026-05-14"


def test_frontmatter_toggle_off() -> None:
    note = render(_session([Message("human", "Add auth")]), _config(frontmatter=False))
    assert not note.markdown.startswith("---")


def test_tagging_toggle() -> None:
    msg = [Message("human", "x")]
    on = render(_session(msg), _config(frontmatter=True, tagging=True))
    off = render(_session(msg), _config(frontmatter=True, tagging=False))
    assert "tags" in _parse_frontmatter(on.markdown)
    assert "tags" not in _parse_frontmatter(off.markdown)


def test_wikilink_injection_neutralized() -> None:
    evil = "See [[Secret Vault Note]] and ![[exfil.png]]"
    note = render(_session([Message("human", evil)]), _config())
    assert "[[Secret Vault Note]]" not in note.markdown
    assert "![[exfil.png]]" not in note.markdown
    assert "Secret Vault Note" in note.markdown  # still human-readable


def test_frontmatter_injection_cannot_break_out() -> None:
    evil = 'Weird: title" value\n---\ninjected: PWNED\nmalicious: true'
    note = render(_session([Message("human", evil)]), _config(frontmatter=True))
    fm = _parse_frontmatter(note.markdown)
    assert "injected" not in fm
    assert "malicious" not in fm
    assert fm["source"] == "claude-code"
    assert fm["title"] == 'Weird: title" value'  # first line, safely quoted
