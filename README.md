# alkham

[![PyPI](https://img.shields.io/pypi/v/alkham)](https://pypi.org/project/alkham/)
[![CI](https://github.com/AliAA1444/alkham/actions/workflows/ci.yml/badge.svg)](https://github.com/AliAA1444/alkham/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/alkham)](https://pypi.org/project/alkham/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Frictionless, one-command capture of your AI coding-CLI sessions — Claude
Code _and_ Aider — as readable Markdown notes.** Library-first; Obsidian by
default, but works with any Markdown folder.

> ⚠️ **Security — transcripts are captured _verbatim_.** `alkham` does **not**
> redact. Never capture sessions containing live API keys, tokens, or other
> secrets: they will be written into your notes as-is. (Path-traversal and
> Markdown/YAML-injection from hostile log content _are_ sanitized so a
> transcript can't corrupt your vault — see `docs/ARCHITECTURE.md` §10.)

## Why alkham

Your best architectural reasoning, hard-won debugging insights, and the
*why* behind decisions are trapped in raw JSONL/history files you never read
again (and Claude Code deletes after ~30 days). `alkham` turns those
disposable terminal logs into clean, chronological, **human-legible** notes
you'll actually return to — and it's the **only** tool capturing Claude Code
**and** Aider through one pluggable engine.

## Quickstart

```bash
pip install alkham
alkham init      # pick an output folder + flavor, toggle features
alkham sync      # capture your most recent Claude Code or Aider session
```

```
✓ Captured 2026-05-14_add-jwt-refresh_a1b2c3.md  crowdflow
```

Capture is a single `alkham sync` today; automatic capture (`alkham watch`)
arrives post-launch.

## Works with or without Obsidian

The `obsidian` flavor emits wikilinks, tags, and a zero-orphan Map-of-Content.
The `plain` flavor emits portable Markdown that opens cleanly in VS Code,
Logseq, Notion, or any folder. Every behavior — routing, Auto-MOC, tagging,
frontmatter — is independently **toggleable**, so `alkham` fits an existing
knowledge base instead of overwriting it.

## Use it as a library

```python
from alkham.parsers import get_parser_for

session = get_parser_for("chat_log.jsonl").parse()
print(session.messages)            # -> list[Message]
print(session.files_modified)      # tool-use breadcrumbs
```

`get_parser_for` auto-detects the source and raises `UnknownSourceError` on an
unrecognized file. The `Session` dataclass is a stability commitment.

## CLI surface

| Command | Purpose |
|---|---|
| `alkham init` | First-run wizard (output dir, flavor, toggles) |
| `alkham sync [-t FILE] [-n]` | Capture the latest (or a specific) session; `-n` dry-runs |
| `alkham backfill [--since DATE] [--project NAME]` | Batch-capture history |
| `alkham config [--edit]` | Show (or edit) the config |
| `alkham moc --project NAME` | Rebuild a project's MOC |
| `alkham install-close-command` | Install the `/close` prompt (Claude Code) |

## Documentation

- `docs/PRODUCT_SPEC.md` — what it does, for whom, how it feels to use
- `docs/ARCHITECTURE.md` — how it's built (the technical source of truth)
- `docs/ROADMAP.md` — the phased build plan
- `CONTRIBUTING.md` — incl. how to add a parser for a new tool

## License

MIT © Ali Alkhamees
