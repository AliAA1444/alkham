"""Phase A (v0.2.0) — parser-driven discovery registry."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from alkham.config import Config, OutputConfig
from alkham.parsers.base import _DISCOVERERS, discoverers, register_discovery
from alkham.sync import find_transcripts


@pytest.fixture
def _restore_discoverers() -> Iterator[None]:
    saved = dict(_DISCOVERERS)
    try:
        yield
    finally:
        _DISCOVERERS.clear()
        _DISCOVERERS.update(saved)


def test_builtin_discoverers_registered() -> None:
    keys = discoverers().keys()
    assert "claude-code" in keys
    assert "aider" in keys


def test_find_transcripts_filters_by_sources(
    tmp_path: Path, _restore_discoverers: None
) -> None:
    marker = tmp_path / "found.txt"
    marker.write_text("x", encoding="utf-8")
    register_discovery("dummy", lambda config: [marker])

    off = Config(output=OutputConfig(base_path=str(tmp_path)), sources=["claude-code"])
    assert marker not in find_transcripts(off)

    on = Config(output=OutputConfig(base_path=str(tmp_path)), sources=["dummy"])
    assert marker in find_transcripts(on)
