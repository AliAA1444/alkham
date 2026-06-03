"""alkham — capture AI coding-CLI sessions as readable Markdown notes.

The public library API is re-exported here: the typed ``Session`` (plus
``Message``/``RenderedNote``) and the ``get_parser_for``/``register`` seam.
"""

from __future__ import annotations

from alkham.models import Message, RenderedNote, Session
from alkham.parsers import get_parser_for, register

__version__ = "0.1.0"

__all__ = [
    "Message",
    "RenderedNote",
    "Session",
    "__version__",
    "get_parser_for",
    "register",
]
