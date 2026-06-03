"""Pure routing — decide where a captured session belongs.

No I/O. Because ``cwd``/project come from possibly-untrusted transcript
content, the decoded project name is sanitized to a single safe path segment,
and the resolved output path is asserted to stay under the configured base
(raising ``RoutingError`` otherwise) — so a hostile log can never escape the
vault. When routing is disabled, everything goes to the single configured base.
"""

from __future__ import annotations

import re
from pathlib import Path

from alkham.config import Config
from alkham.errors import RoutingError
from alkham.models import Session

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_SEPARATORS = re.compile(r"[\\/]+")


def decode_project(cwd: str | None) -> str:
    """Return the last path component of ``cwd`` (the raw project name)."""
    if not cwd:
        return ""
    segments: list[str] = [s for s in re.split(r"[\\/]+", cwd.strip()) if s]
    return segments[-1] if segments else ""


def sanitize_segment(name: str) -> str:
    """Reduce a decoded name to a single safe path segment (no traversal)."""
    cleaned = _CONTROL.sub("", name)
    cleaned = _SEPARATORS.sub("-", cleaned)
    return cleaned.strip(" .-")


def is_blocklisted(name: str, blocklist: list[str]) -> bool:
    """Case-insensitive membership test against the blocklist."""
    lowered = {b.lower() for b in blocklist}
    return name.lower() in lowered


def resolve_output_dir(session: Session, config: Config) -> Path:
    """Resolve the directory a session's note is written to (pure, no I/O)."""
    base = Path(config.output.base_path)
    if not config.features.routing:
        return _within(base, base)

    project = sanitize_segment(decode_project(session.cwd))
    if not project or is_blocklisted(project, config.blocklist):
        candidate = base / config.output.inbox_subdir
    else:
        candidate = base / config.output.projects_subdir / project / "sessions"
    return _within(base, candidate)


def _within(base: Path, candidate: Path) -> Path:
    """Guarantee ``candidate`` stays under ``base`` or raise ``RoutingError``."""
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError:
        raise RoutingError(
            f"refusing to write outside the configured base: {candidate}"
        ) from None
    return candidate
