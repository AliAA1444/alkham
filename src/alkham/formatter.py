"""Session -> RenderedNote. Pure. Escapes untrusted transcript content.

Builds optional YAML frontmatter (safe-serialized), a readable header, tool
breadcrumbs, and the conversation. Untrusted message/field content is run
through ``neutralize`` so embedded ``[[wikilinks]]`` / ``![[embeds]]`` cannot
inject into the vault graph; frontmatter is emitted via ``yaml.safe_dump`` so a
value can never break out of the frontmatter block.
"""

from __future__ import annotations

import yaml

from alkham.config import Config
from alkham.flavors import get_flavor
from alkham.models import RenderedNote, Session
from alkham.routing import sanitize_segment
from alkham.titles import make_filename, slugify, title_for

_HUMAN = "## 👤 You"
_ASSISTANT = "## 🤖 Assistant"


def neutralize(text: str) -> str:
    """Break Obsidian wikilink/embed openers in untrusted content."""
    return text.replace("[[", "[\\[")


def _inline_code(value: str) -> str:
    return "`" + neutralize(value).replace("`", "ʼ") + "`"


def render(session: Session, config: Config) -> RenderedNote:
    flavor = get_flavor(config.output.flavor)
    title = title_for(session)
    parts: list[str] = []

    if config.features.frontmatter:
        parts.append(_frontmatter(session, config, title))

    parts.append(f"# {neutralize(title)}")
    if flavor.obsidian:
        moc = f"{sanitize_segment(session.project) or 'inbox'}-MOC"
        parts.append(f"> 🗂️ {flavor.link(moc)}")
    parts.append(_meta_line(session))

    breadcrumbs = _breadcrumbs(session)
    if breadcrumbs:
        parts.append(breadcrumbs)

    parts.append("---")
    parts.append(_conversation(session))

    markdown = "\n\n".join(part for part in parts if part).rstrip() + "\n"
    return RenderedNote(
        filename=make_filename(session),
        markdown=markdown,
        project=session.project,
    )


def _frontmatter(session: Session, config: Config, title: str) -> str:
    data: dict[str, object] = {
        "title": neutralize(title),
        "source": session.source,
        "project": neutralize(session.project),
    }
    date = (session.started_at or "")[:10]
    if date:
        data["date"] = date
    if session.model:
        data["model"] = neutralize(session.model)
    if config.features.tagging:
        data["tags"] = _tags(session)
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{body}\n---"


def _tags(session: Session) -> list[str]:
    tags = ["alkham/session", session.source]
    if session.project:
        tags.append(f"project/{slugify(session.project)}")
    return tags


def _meta_line(session: Session) -> str:
    bits = [
        f"**Source:** {session.source}",
        f"**Project:** {neutralize(session.project)}",
    ]
    date = (session.started_at or "")[:10]
    if date:
        bits.append(f"**Date:** {date}")
    if session.model:
        bits.append(f"**Model:** {neutralize(session.model)}")
    return "> " + " · ".join(bits)


def _breadcrumbs(session: Session) -> str:
    lines: list[str] = []
    if session.files_modified:
        lines.append("**Files touched:**")
        lines += [f"- {_inline_code(path)}" for path in session.files_modified]
    if session.commands_run:
        lines.append("**Commands run:**")
        lines += [f"- {_inline_code(cmd)}" for cmd in session.commands_run]
    return "\n".join(lines)


def _conversation(session: Session) -> str:
    blocks: list[str] = []
    for message in session.messages:
        header = _HUMAN if message.role == "human" else _ASSISTANT
        blocks.append(f"{header}\n\n{neutralize(message.content).strip()}")
    return "\n\n".join(blocks)
