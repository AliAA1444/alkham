"""Typed exceptions.

Library/pure functions raise these; they never call ``sys.exit`` or print.
The CLI catches ``AlkhamError`` at the top level and renders a clean message
with a nonzero exit code. Library consumers catch the same typed exceptions.
"""

from __future__ import annotations


class AlkhamError(Exception):
    """Base class for every alkham error."""


class ConfigError(AlkhamError):
    """Configuration is missing or invalid (e.g. run ``alkham init``)."""


class ParseError(AlkhamError):
    """A transcript could not be parsed."""


class RoutingError(AlkhamError):
    """A session could not be safely routed to an output path."""


class UnknownSourceError(ParseError):
    """No registered parser recognized the transcript file."""
