"""Phase 4 — the Aider parser (THE MOAT): multi-session split + idempotency."""

from __future__ import annotations

from pathlib import Path

from alkham.config import Config, OutputConfig
from alkham.parsers import get_parser_for
from alkham.parsers.aider import AiderParser
from alkham.routing import resolve_output_dir
from alkham.titles import make_filename

FIXTURES = Path(__file__).parent / "fixtures"
AIDER = FIXTURES / "aider-history.md"


def test_splits_into_multiple_sessions() -> None:
    sessions = AiderParser().parse_all(AIDER)
    assert len(sessions) == 2
    assert sessions[0].started_at == "2026-05-14 09:15:32"
    assert sessions[1].started_at == "2026-05-14 14:22:10"
    assert all(s.source == "aider" for s in sessions)


def test_first_session_messages() -> None:
    s = AiderParser().parse_all(AIDER)[0]
    assert [m.role for m in s.messages] == ["human", "assistant", "human", "assistant"]
    assert s.messages[0].content == "Implement a fibonacci function"
    assert "iterative fibonacci" in s.messages[1].content
    assert "```python" in s.messages[1].content


def test_parse_returns_most_recent() -> None:
    s = AiderParser().parse(AIDER)
    assert s.started_at == "2026-05-14 14:22:10"
    assert s.messages[0].content == "Fix the off-by-one in the parser"


def test_session_ids_distinct_and_idempotent() -> None:
    ids_a = [s.session_id for s in AiderParser().parse_all(AIDER)]
    ids_b = [s.session_id for s in AiderParser().parse_all(AIDER)]
    assert ids_a == ids_b
    assert len(set(ids_a)) == len(ids_a)


def test_appended_session_yields_new_id(tmp_path: Path) -> None:
    base = AIDER.read_text(encoding="utf-8")
    p = tmp_path / "crowdflow" / ".aider.chat.history.md"
    p.parent.mkdir(parents=True)
    p.write_text(base, encoding="utf-8")
    before = [s.session_id for s in AiderParser().parse_all(p)]

    appended = (
        base
        + "\n# aider chat started at 2026-05-15 08:00:00\n\n#### New work\n\nReply.\n"
    )
    p.write_text(appended, encoding="utf-8")
    after = [s.session_id for s in AiderParser().parse_all(p)]

    assert after[: len(before)] == before
    assert len(after) == len(before) + 1
    assert after[-1] not in before


def test_project_from_directory(tmp_path: Path) -> None:
    p = tmp_path / "crowdflow" / ".aider.chat.history.md"
    p.parent.mkdir(parents=True)
    p.write_text(AIDER.read_text(encoding="utf-8"), encoding="utf-8")
    assert AiderParser().parse(p).project == "crowdflow"


def test_get_parser_for_disambiguates() -> None:
    assert get_parser_for(AIDER).source_name == "aider"
    assert get_parser_for(FIXTURES / "claude-basic.jsonl").source_name == "claude-code"


def test_can_parse_rejects_non_aider(tmp_path: Path) -> None:
    plain = tmp_path / "notes.md"
    plain.write_text("# Just some notes\n", encoding="utf-8")
    assert AiderParser().can_parse(plain) is False
    assert AiderParser().can_parse(FIXTURES / "claude-basic.jsonl") is False


def test_downstream_pipeline_unchanged(tmp_path: Path) -> None:
    session = AiderParser().parse(AIDER)
    cfg = Config(output=OutputConfig(base_path=str(tmp_path)))
    out = resolve_output_dir(session, cfg)
    filename = make_filename(session)
    assert tmp_path in out.parents
    assert filename.startswith("2026-05-14_") and filename.endswith(".md")
