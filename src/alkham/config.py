"""Configuration — nested frozen dataclasses, YAML load/save, and the wizard.

The dataclasses are the DI data contract for routing/formatter/moc/sync. This
module also owns persistence (to the platformdirs config dir) and the
interactive ``alkham init`` wizard. The wizard lazily imports ``typer`` so the
pure import path (routing/formatter) stays free of CLI dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs
import yaml

from alkham.errors import ConfigError

CONFIG_FILENAME = "config.yaml"


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
    """The full injected configuration."""

    output: OutputConfig = field(default_factory=OutputConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    sources: list[str] = field(default_factory=_default_sources)
    claude_projects_dir: str = ""
    aider_search_roots: list[str] = field(default_factory=list)
    known_projects: list[str] = field(default_factory=list)
    blocklist: list[str] = field(default_factory=_default_blocklist)
    min_messages: int = 4


# ── Persistence ──────────────────────────────────────────────────────────────


def config_path() -> Path:
    """OS-correct config file path (``platformdirs``)."""
    return Path(platformdirs.user_config_dir("alkham")) / CONFIG_FILENAME


def to_dict(config: Config) -> dict[str, Any]:
    return {
        "output": {
            "flavor": config.output.flavor,
            "base_path": config.output.base_path,
            "projects_subdir": config.output.projects_subdir,
            "inbox_subdir": config.output.inbox_subdir,
        },
        "sources": list(config.sources),
        "claude_projects_dir": config.claude_projects_dir,
        "aider_search_roots": list(config.aider_search_roots),
        "features": {
            "routing": config.features.routing,
            "auto_moc": config.features.auto_moc,
            "tagging": config.features.tagging,
            "artifact_extraction": config.features.artifact_extraction,
            "frontmatter": config.features.frontmatter,
        },
        "known_projects": list(config.known_projects),
        "blocklist": list(config.blocklist),
        "min_messages": config.min_messages,
    }


def from_dict(data: dict[str, Any]) -> Config:
    """Build a Config from a parsed YAML mapping, tolerant of missing keys."""
    out = data.get("output") or {}
    feat = data.get("features") or {}
    base = Config()
    return Config(
        output=OutputConfig(
            flavor=out.get("flavor", base.output.flavor),
            base_path=out.get("base_path", base.output.base_path),
            projects_subdir=out.get("projects_subdir", base.output.projects_subdir),
            inbox_subdir=out.get("inbox_subdir", base.output.inbox_subdir),
        ),
        features=FeatureFlags(
            routing=feat.get("routing", base.features.routing),
            auto_moc=feat.get("auto_moc", base.features.auto_moc),
            tagging=feat.get("tagging", base.features.tagging),
            artifact_extraction=feat.get(
                "artifact_extraction", base.features.artifact_extraction
            ),
            frontmatter=feat.get("frontmatter", base.features.frontmatter),
        ),
        sources=list(data.get("sources", base.sources)),
        claude_projects_dir=data.get("claude_projects_dir", base.claude_projects_dir),
        aider_search_roots=list(
            data.get("aider_search_roots", base.aider_search_roots)
        ),
        known_projects=list(data.get("known_projects", base.known_projects)),
        blocklist=list(data.get("blocklist", base.blocklist)),
        min_messages=int(data.get("min_messages", base.min_messages)),
    )


def save_config(config: Config, path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(to_dict(config), sort_keys=False, allow_unicode=True)
    target.write_text(body, encoding="utf-8")
    return target


def load_config(path: Path | None = None) -> Config:
    source = path or config_path()
    if not source.exists():
        raise ConfigError(f"No config found at {source}. Run `alkham init` first.")
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    return from_dict(data)


# ── Wizard ───────────────────────────────────────────────────────────────────


def build_config(
    base_path: str | Path,
    flavor: str = "obsidian",
    *,
    routing: bool = True,
    auto_moc: bool = True,
    tagging: bool = True,
    frontmatter: bool = True,
    artifact_extraction: bool = True,
    min_messages: int = 4,
    known_projects: list[str] | None = None,
    claude_projects_dir: str | None = None,
    aider_search_roots: list[str] | None = None,
) -> Config:
    """Pure config assembly from explicit answers (no prompts, no I/O)."""
    default_claude = str(Path.home() / ".claude" / "projects")
    return Config(
        output=OutputConfig(flavor=flavor, base_path=str(base_path)),
        features=FeatureFlags(
            routing=routing,
            auto_moc=auto_moc,
            tagging=tagging,
            artifact_extraction=artifact_extraction,
            frontmatter=frontmatter,
        ),
        min_messages=min_messages,
        known_projects=list(known_projects or []),
        claude_projects_dir=(
            claude_projects_dir if claude_projects_dir is not None else default_claude
        ),
        aider_search_roots=list(aider_search_roots or []),
    )


def detect_obsidian_vault() -> Path | None:
    """Best-effort detection of an Obsidian vault in common locations."""
    candidates = [Path.home() / "Documents" / "Obsidian", Path.home() / "Obsidian"]
    for candidate in candidates:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def run_init_wizard(path: Path | None = None) -> Config:
    """Interactive first-run wizard. Returns and persists the new Config."""
    import typer  # lazy: keep the pure import path CLI-free

    detected = detect_obsidian_vault()
    if detected and typer.confirm(
        f"Use detected Obsidian vault at {detected}?", default=True
    ):
        base_path = str(detected)
        default_flavor = "obsidian"
    else:
        base_path = typer.prompt("Output directory (any folder)")
        default_flavor = "plain"

    flavor = typer.prompt("Flavor (obsidian/plain)", default=default_flavor)
    if flavor not in ("obsidian", "plain"):
        flavor = "plain"

    routing = typer.confirm("Enable project routing?", default=True)
    auto_moc = typer.confirm(
        "Enable Auto-MOC (Obsidian graph)?", default=(flavor == "obsidian")
    )
    tagging = typer.confirm("Add tags to frontmatter?", default=True)
    frontmatter = typer.confirm("Write YAML frontmatter?", default=True)

    config = build_config(
        base_path,
        flavor,
        routing=routing,
        auto_moc=auto_moc,
        tagging=tagging,
        frontmatter=frontmatter,
    )
    saved = save_config(config, path)
    typer.echo(f"✓ Config written to {saved}")
    return config
