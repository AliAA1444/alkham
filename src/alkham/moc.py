"""Map-of-Content — pure ``plan_moc_update`` + thin ``ensure_linked`` I/O.

A per-project MOC hub keeps the Obsidian graph orphan-free. Disable-able via
``features.auto_moc`` and off for the ``plain`` flavor (a MOC is an
Obsidian-graph feature). The decision/idempotency logic is pure and unit-tested;
only ``ensure_linked`` touches the filesystem.
"""

from __future__ import annotations

from pathlib import Path

from alkham.config import Config
from alkham.flavors import get_flavor
from alkham.models import RenderedNote
from alkham.routing import sanitize_segment


def moc_enabled(config: Config) -> bool:
    """On only when ``auto_moc`` is set and the flavor is obsidian."""
    return config.features.auto_moc and config.output.flavor != "plain"


def _stem(note: RenderedNote) -> str:
    return note.filename[:-3] if note.filename.endswith(".md") else note.filename


def _moc_path(note: RenderedNote, config: Config) -> Path:
    base = Path(config.output.base_path)
    seg = sanitize_segment(note.project) or "inbox"
    if config.features.routing:
        return base / config.output.projects_subdir / seg / f"{seg}-MOC.md"
    return base / f"{seg}-MOC.md"


def plan_moc_update(existing: str, note: RenderedNote, config: Config) -> str | None:
    """Pure: the new MOC text, or ``None`` if the note is already linked."""
    flavor = get_flavor(config.output.flavor)
    stem = _stem(note)
    link_line = f"- {flavor.link(stem)}"
    if existing:
        if stem in existing:
            return None  # idempotent: already linked
        return existing.rstrip() + "\n" + link_line + "\n"
    seg = sanitize_segment(note.project) or "inbox"
    return f"# {seg} — Map of Content\n\n{link_line}\n"


def ensure_linked(note: RenderedNote, config: Config) -> None:
    """Thin I/O: write the planned MOC update when MOC is enabled."""
    if not moc_enabled(config):
        return
    path = _moc_path(note, config)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = plan_moc_update(existing, note, config)
    if updated is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def rebuild_project_moc(project: str, config: Config) -> int:
    """Re-link every session note in a project into its MOC. Returns the count."""
    if not moc_enabled(config):
        return 0
    base = Path(config.output.base_path)
    seg = sanitize_segment(project) or "inbox"
    sessions_dir = base / config.output.projects_subdir / seg / "sessions"
    if not sessions_dir.is_dir():
        return 0
    count = 0
    for note_file in sorted(sessions_dir.glob("*.md")):
        note = RenderedNote(filename=note_file.name, markdown="", project=project)
        ensure_linked(note, config)
        count += 1
    return count
