"""Phase 2 — the Claude Code JSONL parser."""

from __future__ import annotations

from pathlib import Path

from alkham.models import Session
from alkham.parsers import get_parser_for
from alkham.parsers.claude_code import ClaudeCodeParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str) -> Session:
    return ClaudeCodeParser().parse(FIXTURES / name)


def test_basic_conversation() -> None:
    s = _parse("claude-basic.jsonl")
    assert s.source == "claude-code"
    assert s.session_id == "claude-basic"
    assert s.project == "crowdflow"
    assert s.cwd == "/Users/ali/code/crowdflow"
    assert [m.role for m in s.messages] == ["human", "assistant", "human"]
    assert s.messages[0].content == "Add a health check endpoint"
    assert s.model == "claude-opus-4-8"
    assert s.started_at == "2026-05-14T10:00:00.000Z"
    assert s.ended_at == "2026-05-14T10:01:00.000Z"


def test_tool_extraction() -> None:
    s = _parse("claude-with-tools.jsonl")
    # tool-result-only user turn and tool-use-only assistant turn are not messages
    assert [m.role for m in s.messages] == ["human", "assistant", "assistant"]
    assert s.tools_used == {"Read": 1, "Edit": 1, "Bash": 1, "Write": 1}
    assert s.files_modified == [
        "/Users/ali/code/crowdflow/auth.py",
        "/Users/ali/code/crowdflow/auth_helpers.py",
    ]
    assert s.commands_run == ["pytest -q tests/"]


def test_project_decoding() -> None:
    assert _parse("claude-basic.jsonl").project == "crowdflow"
    assert _parse("claude-noise-only.jsonl").project == "tmp"


def test_noise_only_transcript() -> None:
    s = _parse("claude-noise-only.jsonl")
    assert [m.content for m in s.messages] == [
        "/clear",
        "/model claude-opus-4-8",
        "/exit",
    ]
    assert s.tools_used == {}
    assert s.files_modified == []


def test_malformed_lines_skipped(tmp_path: Path) -> None:
    lines = [
        '{"type":"user","cwd":"/tmp/demo","timestamp":"2026-05-14T09:00:00Z",'
        '"message":{"role":"user","content":"hello"}}',
        "this is not valid json {{{",
        "",
        '{"type":"assistant","cwd":"/tmp/demo","timestamp":"2026-05-14T09:00:01Z",'
        '"message":{"role":"assistant","content":[{"type":"text","text":"hi"}]}}',
    ]
    p = tmp_path / "claude-broken.jsonl"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    s = ClaudeCodeParser().parse(p)
    assert [m.role for m in s.messages] == ["human", "assistant"]
    assert s.project == "demo"


def test_get_parser_for_routes_to_claude() -> None:
    bound = get_parser_for(FIXTURES / "claude-basic.jsonl")
    assert bound.source_name == "claude-code"
    session = bound.parse()
    assert session.project == "crowdflow"
    assert len(bound.parse_all()) == 1
