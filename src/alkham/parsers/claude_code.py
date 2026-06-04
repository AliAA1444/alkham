"""Claude Code JSONL parser.

Owns all Claude-specific knowledge: line ``type`` values, the content-block
message structure, tool-use extraction, and project decoding. Each ``.jsonl``
file is a single session, so ``parse_all()`` returns ``[parse()]``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from alkham.models import Message, Session
from alkham.parsers.base import register, register_discovery

if TYPE_CHECKING:
    from alkham.config import Config

_CLAUDE_TYPES = {"user", "assistant", "summary", "system"}
_FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _extract_text(content: Any) -> str:
    """Join the text blocks of a message; ignore tool_use/tool_result blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        return "\n".join(p for p in parts if isinstance(p, str) and p)
    return ""


def _blocks(content: Any) -> list[Any]:
    """Return the dict content blocks of a message (or an empty list)."""
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _project_from_cwd(cwd: str | None) -> str | None:
    if not cwd:
        return None
    return Path(cwd).name or None


def _project_from_dir(dirname: str) -> str:
    # ~/.claude/projects/<encoded-cwd>, e.g. "-Users-ali-code-crowdflow" -> "crowdflow"
    return dirname.rstrip("-").split("-")[-1] or "unknown"


class ClaudeCodeParser:
    """Parses a Claude Code ``*.jsonl`` transcript into a single Session."""

    source_name = "claude-code"

    def can_parse(self, path: Path) -> bool:
        if path.suffix != ".jsonl":
            return False
        if ".claude" in path.parts and "projects" in path.parts:
            return True
        try:
            with path.open(encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 20:
                        break
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        obj = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    if (
                        isinstance(obj, dict)
                        and obj.get("type") in _CLAUDE_TYPES
                        and ("message" in obj or "sessionId" in obj or "uuid" in obj)
                    ):
                        return True
        except OSError:
            return False
        return False

    def parse(self, path: Path) -> Session:
        cwd: str | None = None
        messages: list[Message] = []
        files_modified: list[str] = []
        commands_run: list[str] = []
        tools_used: dict[str, int] = {}
        model: str | None = None
        timestamps: list[str] = []

        for raw in path.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue  # skip malformed lines, never crash
            if not isinstance(obj, dict):
                continue

            c = obj.get("cwd")
            if isinstance(c, str) and c:
                cwd = c
            t = obj.get("timestamp")
            ts: str | None = t if isinstance(t, str) and t else None
            if ts:
                timestamps.append(ts)

            mtype = obj.get("type")
            message = obj.get("message")
            if not isinstance(message, dict):
                continue

            if mtype == "user":
                text = _extract_text(message.get("content"))
                if text.strip():
                    messages.append(Message("human", text, ts))
            elif mtype == "assistant":
                m = message.get("model")
                if isinstance(m, str) and m:
                    model = m
                content = message.get("content")
                text = _extract_text(content)
                if text.strip():
                    messages.append(Message("assistant", text, ts))
                self._collect_tools(content, tools_used, files_modified, commands_run)

        project = _project_from_cwd(cwd) or _project_from_dir(path.parent.name)
        return Session(
            session_id=path.stem,
            source=self.source_name,
            project=project,
            cwd=cwd,
            messages=messages,
            files_modified=files_modified,
            commands_run=commands_run,
            tools_used=tools_used,
            started_at=min(timestamps) if timestamps else None,
            ended_at=max(timestamps) if timestamps else None,
            model=model,
        )

    @staticmethod
    def _collect_tools(
        content: Any,
        tools_used: dict[str, int],
        files_modified: list[str],
        commands_run: list[str],
    ) -> None:
        for block in _blocks(content):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if not (isinstance(name, str) and name):
                continue
            tools_used[name] = tools_used.get(name, 0) + 1
            inp = block.get("input")
            if not isinstance(inp, dict):
                continue
            if name in _FILE_TOOLS:
                fp = inp.get("file_path") or inp.get("notebook_path")
                if isinstance(fp, str) and fp and fp not in files_modified:
                    files_modified.append(fp)
            elif name == "Bash":
                cmd = inp.get("command")
                if isinstance(cmd, str) and cmd and cmd not in commands_run:
                    commands_run.append(cmd)

    def parse_all(self, path: Path) -> list[Session]:
        return [self.parse(path)]


def _discover(config: Config) -> list[Path]:
    """Find Claude Code JSONL transcripts under the configured projects dir."""
    if not config.claude_projects_dir:
        return []
    root = Path(config.claude_projects_dir)
    return list(root.rglob("*.jsonl")) if root.is_dir() else []


register(ClaudeCodeParser())
register_discovery("claude-code", _discover)
