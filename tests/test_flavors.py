"""Phase 5 — flavor dialects; the plain flavor stays Obsidian-free."""

from __future__ import annotations

from alkham.config import Config, FeatureFlags, OutputConfig
from alkham.flavors import get_flavor
from alkham.formatter import render
from alkham.models import Message, Session


def _session() -> Session:
    return Session(
        session_id="abc",
        source="aider",
        project="crowdflow",
        started_at="2026-05-14T10:00:00Z",
        messages=[Message("human", "Add a feature"), Message("assistant", "Done")],
    )


def _render(flavor: str) -> str:
    cfg = Config(
        output=OutputConfig(flavor=flavor, base_path="/v"),
        features=FeatureFlags(),
    )
    return render(_session(), cfg).markdown


def test_obsidian_flavor_uses_wikilinks() -> None:
    assert "[[" in _render("obsidian")  # at least the MOC backlink


def test_plain_flavor_is_obsidian_free() -> None:
    assert "[[" not in _render("plain")


def test_plain_neutralizes_injected_wikilinks() -> None:
    s = Session(
        session_id="x",
        source="claude-code",
        project="p",
        messages=[Message("human", "look [[evil]]")],
    )
    cfg = Config(output=OutputConfig(flavor="plain", base_path="/v"))
    assert "[[evil]]" not in render(s, cfg).markdown


def test_flavor_link_dialects() -> None:
    assert get_flavor("obsidian").link("note") == "[[note]]"
    assert get_flavor("plain").link("note") == "[note](note.md)"
    assert get_flavor("unknown").name == "plain"  # fallback
