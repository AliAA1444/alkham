"""Phase 6 — config persistence + wizard config assembly."""

from __future__ import annotations

from pathlib import Path

import pytest

from alkham.config import build_config, from_dict, load_config, save_config, to_dict
from alkham.errors import ConfigError


def test_save_load_roundtrip(tmp_path: Path) -> None:
    cfg = build_config(tmp_path / "vault", "obsidian", auto_moc=True, tagging=False)
    path = tmp_path / "config.yaml"
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.output.flavor == "obsidian"
    assert loaded.output.base_path == str(tmp_path / "vault")
    assert loaded.features.tagging is False
    assert loaded.features.auto_moc is True


def test_build_config_plain_toggles() -> None:
    cfg = build_config("/notes", "plain", routing=False, frontmatter=False)
    assert cfg.output.flavor == "plain"
    assert cfg.features.routing is False
    assert cfg.features.frontmatter is False


def test_from_dict_defaults_when_empty() -> None:
    cfg = from_dict({})
    assert cfg.output.flavor == "obsidian"
    assert cfg.min_messages == 4
    assert "claude-code" in cfg.sources


def test_to_dict_schema_shape() -> None:
    data = to_dict(build_config("/v", "obsidian"))
    assert data["output"]["flavor"] == "obsidian"
    assert data["features"]["routing"] is True
    assert isinstance(data["blocklist"], list)


def test_load_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "absent.yaml")
