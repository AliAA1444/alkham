"""Phase 3 — table-driven tests for routing + path-traversal hardening."""

from __future__ import annotations

from pathlib import Path

import pytest

from alkham.config import Config, FeatureFlags, OutputConfig
from alkham.errors import RoutingError
from alkham.models import Session
from alkham.routing import (
    decode_project,
    is_blocklisted,
    resolve_output_dir,
    sanitize_segment,
)

_BLOCK = ["", "home", "workspace", "downloads", "tmp", "scratch"]


def _session(cwd: str | None) -> Session:
    return Session(session_id="x", source="claude-code", project="", cwd=cwd)


def _config(base: Path, *, routing: bool = True) -> Config:
    return Config(
        output=OutputConfig(
            base_path=str(base),
            projects_subdir="10-Projects",
            inbox_subdir="00-Inbox/unsorted",
        ),
        features=FeatureFlags(routing=routing),
        blocklist=list(_BLOCK),
    )


@pytest.mark.parametrize(
    "cwd,expected",
    [
        ("/Users/ali/code/crowdflow", "crowdflow"),
        ("/Users/ali/code/crowdflow/", "crowdflow"),
        ("/Users/ali/Downloads", "Downloads"),
        ("/", ""),
        (None, ""),
        ("/a/b/..", ".."),
    ],
)
def test_decode_project(cwd: str | None, expected: str) -> None:
    assert decode_project(cwd) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("crowdflow", "crowdflow"),
        ("..", ""),
        ("../../etc", "etc"),
        ("a/b", "a-b"),
        ("\x00\x01evil", "evil"),
        ("  spaced  ", "spaced"),
        (".hidden", "hidden"),
        ("my-project", "my-project"),
    ],
)
def test_sanitize_segment(raw: str, expected: str) -> None:
    assert sanitize_segment(raw) == expected


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Downloads", True),
        ("downloads", True),
        ("DOWNLOADS", True),
        ("crowdflow", False),
        ("", True),
    ],
)
def test_is_blocklisted_case_insensitive(name: str, expected: bool) -> None:
    assert is_blocklisted(name, _BLOCK) == expected


def test_routing_known_project(tmp_path: Path) -> None:
    out = resolve_output_dir(_session("/Users/ali/code/crowdflow"), _config(tmp_path))
    assert out == tmp_path / "10-Projects" / "crowdflow" / "sessions"


@pytest.mark.parametrize(
    "cwd",
    ["/Users/ali/Downloads", "/Users/ali/TMP", "/home", "/Users/x/Workspace"],
)
def test_routing_blocklisted_to_inbox(tmp_path: Path, cwd: str) -> None:
    out = resolve_output_dir(_session(cwd), _config(tmp_path))
    assert out == tmp_path / "00-Inbox/unsorted"


def test_routing_off_returns_base(tmp_path: Path) -> None:
    cfg = _config(tmp_path, routing=False)
    out = resolve_output_dir(_session("/Users/ali/code/crowdflow"), cfg)
    assert out == tmp_path


@pytest.mark.parametrize(
    "cwd",
    [
        "/Users/ali/code/../../../../etc",
        "/Users/ali/../../../../../../etc/passwd",
        "/a/b/..",
    ],
)
def test_routing_hostile_cwd_stays_contained(tmp_path: Path, cwd: str) -> None:
    out = resolve_output_dir(_session(cwd), _config(tmp_path)).resolve()
    base = tmp_path.resolve()
    assert out == base or base in out.parents


def test_routing_backstop_rejects_escaping_subdir(tmp_path: Path) -> None:
    cfg = Config(
        output=OutputConfig(
            base_path=str(tmp_path),
            projects_subdir="../../escape",
            inbox_subdir="inbox",
        ),
        features=FeatureFlags(routing=True),
        blocklist=list(_BLOCK),
    )
    with pytest.raises(RoutingError):
        resolve_output_dir(_session("/Users/ali/code/crowdflow"), cfg)
