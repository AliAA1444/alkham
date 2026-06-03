"""Phase 6 — sync orchestration end-to-end against a temp vault."""

from __future__ import annotations

import os
import time
from pathlib import Path

from alkham.backfill import backfill
from alkham.config import build_config
from alkham.sync import capture, find_transcripts, latest_transcript

FIXTURES = Path(__file__).parent / "fixtures"


def test_capture_claude_writes_routed_note(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=1)
    note = capture(FIXTURES / "claude-basic.jsonl", cfg)
    assert note is not None
    written = list(tmp_path.rglob("*.md"))
    assert any(p.name == note.filename for p in written)
    assert any("crowdflow" in str(p) for p in written)  # routed by project


def test_capture_aider_writes_most_recent(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=1)
    note = capture(FIXTURES / "aider-history.md", cfg)
    assert note is not None
    body = next(tmp_path.rglob(note.filename)).read_text(encoding="utf-8")
    assert "Fix the off-by-one" in body


def test_below_threshold_skipped(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=99)
    assert capture(FIXTURES / "claude-basic.jsonl", cfg) is None
    assert not list(tmp_path.rglob("*.md"))


def test_toggle_frontmatter_off_plain(tmp_path: Path) -> None:
    cfg = build_config(
        tmp_path, "plain", min_messages=1, frontmatter=False, auto_moc=False
    )
    note = capture(FIXTURES / "claude-basic.jsonl", cfg)
    assert note is not None
    text = next(tmp_path.rglob(note.filename)).read_text(encoding="utf-8")
    assert not text.startswith("---")
    assert "[[" not in text


def test_routing_off_writes_to_base(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=1, routing=False)
    note = capture(FIXTURES / "claude-basic.jsonl", cfg)
    assert note is not None
    assert (tmp_path / note.filename).exists()


def test_find_and_latest_transcript(tmp_path: Path) -> None:
    claude_dir = tmp_path / "claude" / "proj"
    claude_dir.mkdir(parents=True)
    jsonl = claude_dir / "session.jsonl"
    jsonl.write_text(
        '{"type":"user","message":{"role":"user","content":"hi"}}\n', encoding="utf-8"
    )
    aider_root = tmp_path / "code" / "myproj"
    aider_root.mkdir(parents=True)
    aider = aider_root / ".aider.chat.history.md"
    aider.write_text(
        "# aider chat started at 2026-01-01 00:00:00\n\n#### hi\n\nyo\n",
        encoding="utf-8",
    )
    future = time.time() + 10
    os.utime(aider, (future, future))  # make the aider file newest

    cfg = build_config(
        tmp_path / "v",
        "obsidian",
        claude_projects_dir=str(tmp_path / "claude"),
        aider_search_roots=[str(tmp_path / "code")],
    )
    found = find_transcripts(cfg)
    assert jsonl in found and aider in found
    assert latest_transcript(cfg) == aider


def test_backfill_captures_all_aider_sessions(tmp_path: Path) -> None:
    code = tmp_path / "code" / "proj"
    code.mkdir(parents=True)
    (code / ".aider.chat.history.md").write_text(
        (FIXTURES / "aider-history.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    cfg = build_config(
        tmp_path / "vault",
        "obsidian",
        min_messages=1,
        claude_projects_dir=str(tmp_path / "none"),
        aider_search_roots=[str(tmp_path / "code")],
    )
    assert len(backfill(cfg)) == 2  # both delimited chats captured
    assert len(backfill(cfg, since="2026-05-14")) == 2
    assert backfill(cfg, since="2099-01-01") == []
    assert len(backfill(cfg, project="proj")) == 2
    assert backfill(cfg, project="nonexistent") == []
