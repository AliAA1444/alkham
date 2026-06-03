"""Parser package — registry API re-exports; parsers self-register on import."""

from __future__ import annotations

from alkham.parsers.base import (
    BoundParser,
    TranscriptParser,
    get_parser_for,
    register,
)

from . import aider as _aider  # noqa: F401
from . import claude_code as _claude_code  # noqa: F401

__all__ = ["BoundParser", "TranscriptParser", "get_parser_for", "register"]
