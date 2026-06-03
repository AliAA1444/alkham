"""Configuration dataclasses (nested, frozen).

Phase 3 introduces the data contract that ``routing`` / ``formatter`` / ``moc``
/ ``sync`` receive by dependency injection. YAML load/save and the ``init``
wizard arrive in Phase 6 — this file holds only the typed shape for now.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OutputConfig:
    """Where and in what dialect notes are written."""

    flavor: str = "obsidian"  # obsidian | plain
    base_path: str = ""
    projects_subdir: str = "10-Projects"  # used only when routing is on
    inbox_subdir: str = "00-Inbox/unsorted"  # used only when routing is on


@dataclass(frozen=True)
class FeatureFlags:
    """Independently toggleable behaviors (design principle #4)."""

    routing: bool = True
    auto_moc: bool = True
    tagging: bool = True
    artifact_extraction: bool = True
    frontmatter: bool = True


def _default_sources() -> list[str]:
    return ["claude-code", "aider"]


def _default_blocklist() -> list[str]:
    return ["", "home", "workspace", "downloads", "tmp", "scratch"]


@dataclass(frozen=True)
class Config:
    """The full injected configuration. Constructed from YAML in Phase 6."""

    output: OutputConfig = field(default_factory=OutputConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    sources: list[str] = field(default_factory=_default_sources)
    claude_projects_dir: str = ""
    aider_search_roots: list[str] = field(default_factory=list)
    known_projects: list[str] = field(default_factory=list)
    blocklist: list[str] = field(default_factory=_default_blocklist)
    min_messages: int = 4
