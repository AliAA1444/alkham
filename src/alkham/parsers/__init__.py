"""Parser package — registry API re-exports; parsers self-register on import."""

from __future__ import annotations

from alkham.parsers.base import (
    BoundParser,
    TranscriptParser,
    get_parser_for,
    register,
)

# Concrete parsers self-register on import; they arrive in later phases:
#   from alkham.parsers import claude_code as _claude_code  # noqa: F401  (Phase 2)
#   from alkham.parsers import aider as _aider              # noqa: F401  (Phase 4)

__all__ = ["BoundParser", "TranscriptParser", "get_parser_for", "register"]
