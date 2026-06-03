"""Phase 5 — MOC: idempotent linking, zero orphans, skip when disabled."""

from __future__ import annotations

from pathlib import Path

from alkham.config import Config, FeatureFlags, OutputConfig
from alkham.moc import ensure_linked, moc_enabled, plan_moc_update
from alkham.models import RenderedNote


def _note(
    stem: str = "2026-05-14_add-auth_abc123", project: str = "crowdflow"
) -> RenderedNote:
    return RenderedNote(filename=f"{stem}.md", markdown="...", project=project)


def _config(
    base: Path, *, auto_moc: bool = True, flavor: str = "obsidian", routing: bool = True
) -> Config:
    return Config(
        output=OutputConfig(
            flavor=flavor, base_path=str(base), projects_subdir="10-Projects"
        ),
        features=FeatureFlags(auto_moc=auto_moc, routing=routing),
    )


def test_moc_enabled_matrix(tmp_path: Path) -> None:
    assert moc_enabled(_config(tmp_path, auto_moc=True, flavor="obsidian")) is True
    assert moc_enabled(_config(tmp_path, auto_moc=False, flavor="obsidian")) is False
    assert moc_enabled(_config(tmp_path, auto_moc=True, flavor="plain")) is False


def test_plan_creates_moc_with_link() -> None:
    updated = plan_moc_update("", _note(), _config(Path("/v")))
    assert updated is not None
    assert "[[2026-05-14_add-auth_abc123]]" in updated
    assert "crowdflow" in updated.lower()


def test_plan_relink_is_noop() -> None:
    cfg = _config(Path("/v"))
    first = plan_moc_update("", _note(), cfg)
    assert first is not None
    assert plan_moc_update(first, _note(), cfg) is None  # idempotent


def test_ensure_linked_writes_and_is_idempotent(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    ensure_linked(_note(), cfg)
    moc = tmp_path / "10-Projects" / "crowdflow" / "crowdflow-MOC.md"
    assert moc.exists()
    first = moc.read_text(encoding="utf-8")
    assert "[[2026-05-14_add-auth_abc123]]" in first
    ensure_linked(_note(), cfg)  # re-run
    assert moc.read_text(encoding="utf-8") == first  # no duplicates


def test_ensure_linked_links_multiple_notes_zero_orphans(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    ensure_linked(_note("note-a_aaa"), cfg)
    ensure_linked(_note("note-b_bbb"), cfg)
    moc = (tmp_path / "10-Projects" / "crowdflow" / "crowdflow-MOC.md").read_text()
    assert "[[note-a_aaa]]" in moc and "[[note-b_bbb]]" in moc


def test_ensure_linked_skips_when_disabled(tmp_path: Path) -> None:
    ensure_linked(_note(), _config(tmp_path, auto_moc=False))
    assert not (tmp_path / "10-Projects" / "crowdflow" / "crowdflow-MOC.md").exists()


def test_ensure_linked_skips_for_plain(tmp_path: Path) -> None:
    ensure_linked(_note(), _config(tmp_path, flavor="plain"))
    assert not list(tmp_path.rglob("*-MOC.md"))
