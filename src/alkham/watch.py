"""Filesystem watcher / daemon — auto-capture sessions as they go quiet.

The debounce *decision* is a pure, unit-tested ``DebounceTracker``; only
``run_watch`` touches watchdog + the filesystem (the thin shell). Race-safety
against reading a still-being-written transcript comes from three layers:
debounce-on-stability here, plus the parsers' malformed-line tolerance and
``sync``'s idempotent writes (a too-early partial capture is overwritten by the
complete one on the next quiet window). ``watchdog`` is an optional extra:
``pip install 'alkham[watch]'``.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from alkham.config import Config
from alkham.errors import AlkhamError, ConfigError
from alkham.models import RenderedNote
from alkham.sync import capture

CaptureCallback = Callable[[Path, RenderedNote], None]


class DebounceTracker:
    """Pure debounce: record write times; report paths quiet >= quiet_seconds.

    Thread-safe (watchdog records from its thread; the sweep loop reads from the
    main thread), but the timing logic is deterministic given explicit ``now``.
    """

    def __init__(self, quiet_seconds: float) -> None:
        self.quiet_seconds = quiet_seconds
        self._pending: dict[Path, float] = {}
        self._lock = threading.Lock()

    def record(self, path: Path, now: float) -> None:
        """Note a write to ``path`` at ``now`` (resets its quiet timer)."""
        with self._lock:
            self._pending[path] = now

    def due(self, now: float) -> list[Path]:
        """Return (and clear) paths quiet for >= ``quiet_seconds`` (sorted)."""
        with self._lock:
            ready = sorted(
                p
                for p, last in self._pending.items()
                if now - last >= self.quiet_seconds
            )
            for path in ready:
                del self._pending[path]
        return ready


def _is_transcript(path: Path) -> bool:
    """Cheap event filter for known transcript shapes (Claude/Codex/Aider)."""
    return path.suffix == ".jsonl" or path.name == ".aider.chat.history.md"


def _watch_roots(config: Config) -> list[Path]:
    """Existing directories to watch, derived from the enabled sources."""
    candidates: list[Path] = []
    if "claude-code" in config.sources and config.claude_projects_dir:
        candidates.append(Path(config.claude_projects_dir))
    if "aider" in config.sources:
        candidates.extend(Path(root) for root in config.aider_search_roots)
    seen: set[Path] = set()
    roots: list[Path] = []
    for candidate in candidates:
        if candidate not in seen and candidate.is_dir():
            seen.add(candidate)
            roots.append(candidate)
    return roots


class _RecordingHandler:
    """A watchdog-compatible handler (duck-typed ``dispatch``, no subclassing)."""

    def __init__(self, tracker: DebounceTracker) -> None:
        self._tracker = tracker

    def dispatch(self, event: object) -> None:
        if getattr(event, "is_directory", False):
            return
        src = getattr(event, "src_path", None)
        if isinstance(src, (str, bytes)):
            path = Path(os.fsdecode(src))
            if _is_transcript(path):
                self._tracker.record(path, time.monotonic())


def _sync_one(path: Path, config: Config, on_capture: CaptureCallback | None) -> None:
    """Capture one path; skip unrecognized/erroring files (never crash)."""
    try:
        note = capture(path, config)
    except AlkhamError:
        return
    if note is not None and on_capture is not None:
        on_capture(path, note)


def _make_observer() -> Any:
    try:
        from watchdog.observers import Observer
    except ImportError as exc:  # pragma: no cover - only without the extra
        raise ConfigError(
            "watch mode needs the 'watch' extra: pip install 'alkham[watch]'"
        ) from exc
    return Observer()


def run_watch(
    config: Config,
    *,
    quiet_seconds: float | None = None,
    poll_interval: float = 1.0,
    on_capture: CaptureCallback | None = None,
) -> None:
    """Watch the enabled sources and auto-capture sessions as they go quiet.

    Blocks until ``KeyboardInterrupt`` (Ctrl-C), then stops the observer cleanly.
    """
    quiet = float(quiet_seconds if quiet_seconds is not None else config.quiet_seconds)
    roots = _watch_roots(config)
    if not roots:
        raise ConfigError("No watchable source dirs configured — run `alkham init`.")
    tracker = DebounceTracker(quiet)
    handler = _RecordingHandler(tracker)
    observer = _make_observer()
    for root in roots:
        observer.schedule(handler, str(root), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(poll_interval)
            for path in tracker.due(time.monotonic()):
                _sync_one(path, config, on_capture)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
