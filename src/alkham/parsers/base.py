"""TranscriptParser Protocol + registry + get_parser_for.

The single most important architectural element: a structural contract every
parser satisfies, plus an **import-populated** registry so a new tool is added
by dropping a module into ``parsers/`` (and one self-registration import in
``parsers/__init__.py``) — touching nothing in the core pipeline.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from alkham.errors import UnknownSourceError
from alkham.models import Session

if TYPE_CHECKING:
    from alkham.config import Config


@runtime_checkable
class TranscriptParser(Protocol):
    """Structural contract for a source parser (Claude Code, Aider, …).

    ``runtime_checkable`` only verifies *method names*, so this is a contract
    for parser authors, not an ``isinstance`` gate.
    """

    source_name: str

    def can_parse(self, path: Path) -> bool: ...
    def parse(self, path: Path) -> Session: ...
    def parse_all(self, path: Path) -> list[Session]: ...


_REGISTRY: dict[str, TranscriptParser] = {}


def register(parser: TranscriptParser) -> None:
    """Register ``parser`` under its ``source_name`` (called on import)."""
    _REGISTRY[parser.source_name] = parser


# Per-source discovery: each parser registers where its transcripts live, so
# ``sync.find_transcripts`` is parser-driven (adding a tool stays zero-core-change).
_DISCOVERERS: dict[str, Callable[[Config], Iterable[Path]]] = {}


def register_discovery(
    source_name: str, discover: Callable[[Config], Iterable[Path]]
) -> None:
    """Register a discovery function for ``source_name`` (called on import)."""
    _DISCOVERERS[source_name] = discover


def discoverers() -> dict[str, Callable[[Config], Iterable[Path]]]:
    """Return the registered ``{source_name: discover_fn}`` mapping (a copy)."""
    return dict(_DISCOVERERS)


class BoundParser:
    """A parser bound to a path so ``.parse()``/``.parse_all()`` need no args."""

    def __init__(self, parser: TranscriptParser, path: Path) -> None:
        self._parser = parser
        self._path = path

    @property
    def source_name(self) -> str:
        return self._parser.source_name

    def parse(self) -> Session:
        """Parse the most-recent session in the bound file."""
        return self._parser.parse(self._path)

    def parse_all(self) -> list[Session]:
        """Parse every session in the bound file (Claude→1, Aider→N)."""
        return self._parser.parse_all(self._path)


def get_parser_for(path: str | Path) -> BoundParser:
    """Auto-detect and return a parser bound to ``path``.

    This is the primary public library entrypoint::

        session = get_parser_for("chat_log.jsonl").parse()

    Raises:
        UnknownSourceError: if no registered parser recognizes the file.
    """
    p = Path(path)
    for parser in _REGISTRY.values():
        if parser.can_parse(p):
            return BoundParser(parser, p)
    raise UnknownSourceError(f"No registered parser recognizes {p}")
