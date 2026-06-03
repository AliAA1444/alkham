"""Phase 3 — table-driven tests for noise-skipping titles + filenames."""

from __future__ import annotations

import pytest

from alkham.models import Message, Session
from alkham.titles import is_noise, make_filename, slugify


def _session(messages: list[Message], sid: str, started: str | None) -> Session:
    return Session(
        session_id=sid,
        source="claude-code",
        project="p",
        messages=messages,
        started_at=started,
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("/clear", True),
        ("/model claude-opus-4-8", True),
        ("/exit", True),
        ("", True),
        ("   ", True),
        ("Add a health check endpoint", False),
        ("/Users/ali/path note", False),
    ],
)
def test_is_noise(text: str, expected: bool) -> None:
    assert is_noise(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Add JWT auth", "add-jwt-auth"),
        ("Fix the bug!!!", "fix-the-bug"),
        ("  Multiple   spaces  ", "multiple-spaces"),
        ("Hello_World", "hello-world"),
        ("###", "untitled"),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert slugify(text) == expected


def test_make_filename_format() -> None:
    s = _session([Message("human", "Add JWT auth")], "sess-a", "2026-05-14T10:00:00Z")
    fn = make_filename(s)
    assert fn.startswith("2026-05-14_add-jwt-auth_")
    assert fn.endswith(".md")


def test_make_filename_skips_noise_for_title() -> None:
    msgs = [
        Message("human", "/clear"),
        Message("human", "/model x"),
        Message("human", "Refactor the auth module"),
    ]
    assert "_refactor-the-auth-module_" in make_filename(_session(msgs, "id1", None))


def test_make_filename_collision_resistance() -> None:
    msgs = [Message("human", "Same title")]
    a = make_filename(_session(msgs, "idA", "2026-05-14T10:00:00Z"))
    b = make_filename(_session(msgs, "idB", "2026-05-14T10:00:00Z"))
    assert a != b


def test_make_filename_idempotent() -> None:
    s = _session([Message("human", "Same title")], "idA", "2026-05-14T10:00:00Z")
    assert make_filename(s) == make_filename(s)


def test_make_filename_undated_untitled() -> None:
    s = _session([Message("human", "/clear")], "id1", None)
    assert make_filename(s).startswith("undated_untitled_")
