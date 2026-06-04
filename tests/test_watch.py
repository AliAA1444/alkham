"""Phase C (v0.2.0) — watch mode: debounce + race-safe handoff."""

from __future__ import annotations

from pathlib import Path

import pytest

from alkham.config import build_config
from alkham.errors import ConfigError
from alkham.watch import DebounceTracker, _is_transcript, _sync_one, run_watch

FIXTURES = Path(__file__).parent / "fixtures"


def test_debounce_holds_until_quiet() -> None:
    tracker = DebounceTracker(quiet_seconds=5)
    p = Path("/x/a.jsonl")
    tracker.record(p, 0.0)
    assert tracker.due(3.0) == []      # still being written
    tracker.record(p, 4.0)             # another write resets the timer
    assert tracker.due(7.0) == []      # 7 - 4 = 3 < 5
    assert tracker.due(9.0) == [p]     # 9 - 4 = 5 >= 5 -> due, synced once
    assert tracker.due(20.0) == []     # cleared after firing


def test_due_is_sorted_and_clears() -> None:
    tracker = DebounceTracker(2.0)
    a, b = Path("/x/a.jsonl"), Path("/x/b.jsonl")
    tracker.record(a, 0.0)
    tracker.record(b, 0.0)
    assert tracker.due(2.0) == sorted([a, b])
    assert tracker.due(2.0) == []


def test_is_transcript_filter() -> None:
    assert _is_transcript(Path("/x/session.jsonl"))
    assert _is_transcript(Path("/proj/.aider.chat.history.md"))
    assert not _is_transcript(Path("/x/notes.md"))
    assert not _is_transcript(Path("/x/data.txt"))


def test_sync_one_captures_and_skips_unknown(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=1)
    captured: list[str] = []
    _sync_one(
        FIXTURES / "claude-basic.jsonl",
        cfg,
        lambda _p, note: captured.append(note.filename),
    )
    assert len(captured) == 1
    assert list(tmp_path.rglob("*.md"))

    unknown = tmp_path / "mystery.txt"
    unknown.write_text("not a transcript", encoding="utf-8")
    _sync_one(unknown, cfg, lambda _p, note: captured.append(note.filename))
    assert len(captured) == 1  # unknown source skipped, no crash


def test_partial_write_is_safe_then_corrected(tmp_path: Path) -> None:
    cfg = build_config(tmp_path, "obsidian", min_messages=1)
    live = tmp_path / "live.jsonl"
    live.write_text(
        '{"type":"user","cwd":"/c/proj","timestamp":"2026-05-14T10:00:00Z",'
        '"message":{"role":"user","content":"hi"}}\n'
        '{"type":"assi',  # half-written trailing line
        encoding="utf-8",
    )
    _sync_one(live, cfg, None)  # must not crash on the partial line
    partial = sorted(p.name for p in tmp_path.rglob("*.md"))
    assert partial  # a note was written from the complete line

    live.write_text(
        '{"type":"user","cwd":"/c/proj","timestamp":"2026-05-14T10:00:00Z",'
        '"message":{"role":"user","content":"hi"}}\n'
        '{"type":"assistant","cwd":"/c/proj","timestamp":"2026-05-14T10:00:01Z",'
        '"message":{"role":"assistant","content":[{"type":"text","text":"done"}]}}\n',
        encoding="utf-8",
    )
    _sync_one(live, cfg, None)
    full = sorted(p.name for p in tmp_path.rglob("*.md"))
    assert full == partial  # same filename overwritten, not duplicated


def test_run_watch_raises_without_watchable_roots(tmp_path: Path) -> None:
    cfg = build_config(
        tmp_path,
        "obsidian",
        claude_projects_dir=str(tmp_path / "nonexistent"),
        aider_search_roots=[],
    )
    with pytest.raises(ConfigError):
        run_watch(cfg)
