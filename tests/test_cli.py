"""Phase 6 — CLI smoke tests via Typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from alkham.cli import app
from alkham.config import build_config, save_config

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures"


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.2.0" in result.output


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("init", "sync", "backfill", "config", "moc"):
        assert command in result.output


def test_init_then_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ALKHAM_CONFIG", str(tmp_path / "config.yaml"))
    monkeypatch.setattr("alkham.config.detect_obsidian_vault", lambda: None)
    answers = f"{tmp_path / 'vault'}\nplain\ny\nn\ny\ny\n"
    result = runner.invoke(app, ["init"], input=answers)
    assert result.exit_code == 0, result.output
    assert (tmp_path / "config.yaml").exists()
    shown = runner.invoke(app, ["config"])
    assert shown.exit_code == 0
    assert "flavor: plain" in shown.output


def test_sync_dry_run_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ALKHAM_CONFIG", str(tmp_path / "config.yaml"))
    vault = tmp_path / "vault"
    save_config(build_config(vault, "plain", min_messages=1), tmp_path / "config.yaml")
    result = runner.invoke(
        app, ["sync", "-t", str(FIXTURES / "claude-basic.jsonl"), "-n"]
    )
    assert result.exit_code == 0
    assert "Add a health check" in result.output
    assert not (vault.exists() and list(vault.rglob("*.md")))


def test_sync_writes_note(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ALKHAM_CONFIG", str(tmp_path / "config.yaml"))
    vault = tmp_path / "vault"
    save_config(build_config(vault, "plain", min_messages=1), tmp_path / "config.yaml")
    result = runner.invoke(app, ["sync", "-t", str(FIXTURES / "claude-basic.jsonl")])
    assert result.exit_code == 0
    assert "Captured" in result.output
    assert list(vault.rglob("*.md"))
