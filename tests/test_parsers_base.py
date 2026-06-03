"""Phase 1 — models instantiate and the parser registry/get_parser_for work."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from alkham.errors import UnknownSourceError
from alkham.models import Message, Session
from alkham.parsers import get_parser_for, register
from alkham.parsers.base import _REGISTRY


@pytest.fixture(autouse=True)
def _clean_registry() -> Iterator[None]:
    """Isolate each test from registry mutations."""
    saved = dict(_REGISTRY)
    _REGISTRY.clear()
    try:
        yield
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(saved)


class _DummyParser:
    """A minimal parser that recognizes ``*.dummy`` files."""

    source_name = "dummy"

    def can_parse(self, path: Path) -> bool:
        return path.suffix == ".dummy"

    def parse(self, path: Path) -> Session:
        return Session(session_id="d1", source="dummy", project=path.stem)

    def parse_all(self, path: Path) -> list[Session]:
        return [self.parse(path)]


def test_models_instantiate() -> None:
    msg = Message(role="human", content="hi")
    session = Session(
        session_id="abc",
        source="claude-code",
        project="demo",
        messages=[msg],
    )
    assert session.messages[0].content == "hi"
    assert session.cwd is None
    assert session.tools_used == {}


def test_register_and_get_parser_for() -> None:
    register(_DummyParser())
    bound = get_parser_for("chat.dummy")
    assert bound.source_name == "dummy"
    session = bound.parse()
    assert session.source == "dummy"
    assert session.project == "chat"
    assert len(bound.parse_all()) == 1


def test_get_parser_for_unknown_raises() -> None:
    with pytest.raises(UnknownSourceError):
        get_parser_for("mystery.xyz")


def test_documented_import_path() -> None:
    # The exact public import from ARCHITECTURE §1 must resolve.
    from alkham.parsers import get_parser_for as gpf

    assert callable(gpf)
