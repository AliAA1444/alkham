# 📓 alkham

[![PyPI](https://img.shields.io/pypi/v/alkham)](https://pypi.org/project/alkham/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/alkham/)
[![CI](https://github.com/AliAA1444/alkham/actions/workflows/ci.yml/badge.svg)](https://github.com/AliAA1444/alkham/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Your AI coding sessions are full of hard-won knowledge. `alkham` makes sure
> you never lose it.**

`alkham` automatically turns your **Claude Code** and **Aider** sessions into
clean, readable Markdown notes — filed into your knowledge base while you keep
coding. It's a **local-first CLI** _and_ a **library-first Python engine**, in
one package.

---



https://github.com/user-attachments/assets/dc24eeb9-c232-4280-81cf-7a093c612ecb




## The Problem

Every day you solve real problems with an AI coding agent: an architecture
decided, a gnarly bug traced to its root cause, a working snippet, the
*reasoning* behind a choice. Then… it's gone.

- It's buried in raw `.jsonl` / history files you'll never open again.
- Claude Code **auto-deletes** transcripts after ~30 days.
- It fades from your own memory within days.
- So you re-solve solved problems and forget *why* you made past decisions.

That terminal scrollback is some of your best thinking — and it's evaporating.

## The Solution

**Automated knowledge capture.** `alkham` reads the session your AI tool already
wrote to disk and files a clean, chronological, *human-readable* note into your
Markdown vault — automatically, with zero copy-paste.

```bash
pip install alkham
alkham init      # one-time: pick a folder + flavor
alkham watch     # done — now just code.
```

```
✓ Captured  2026-05-14_add-jwt-refresh_a1b2c3.md    crowdflow
✓ Captured  2026-05-14_fix-race-in-parser_d4e5f6.md  alkham
```

---

## For your Second Brain — zero-touch automation

Run **`alkham watch`** once. Then forget it exists.

You code naturally in Claude Code or Aider. The moment a session wraps up,
`alkham` quietly:

- captures the whole conversation as a **readable narrative**,
- **routes** it to the right project folder in your Obsidian vault,
- **links** it into a per-project Map of Content (zero orphans),
- **tags** it — and every one of these behaviors can be switched off if you
  already have your own system.

No `/save`. No manual export. No friction. Your vault simply **fills itself**
with the context you'll actually want later — and it works with Obsidian **or
any plain Markdown folder** (VS Code, Logseq, Notion, plain files).

> **Local and yours.** No cloud, no account, no telemetry, no network calls.
> Plain Markdown in a folder you own.

## For developers — stop writing log parsers

Under the CLI is a clean, typed engine. Point it at a messy AI log and get a
structured Python object back — in **two lines**:

```python
from alkham.parsers import get_parser_for

session = get_parser_for("chat_log.jsonl").parse()

session.messages        # list[Message]  — clean human / assistant turns
session.files_modified  # which files the agent touched
session.commands_run    # which commands it ran
session.model           # …and more, all typed
```

`alkham` already handles the brittle parts — multiple tools, JSONL vs Markdown
dialects, malformed lines, multi-session history files — so you don't have to.
**It saves you hours of writing and maintaining parsers**, freeing you to build
**custom tools or analytics** on top of your AI logs (compliance,
training-data curation, usage insights, your own integrations):

```python
from pathlib import Path
from alkham.parsers import get_parser_for

# Batch-parse a directory of exported logs into clean, typed objects
for log in Path("exports").glob("*.jsonl"):
    session = get_parser_for(log).parse()
    process(session)   # feed your own pipeline
```

The `Session` dataclass is a **stability commitment** (additive changes only),
and `get_parser_for` auto-detects the source — raising a typed
`UnknownSourceError` on anything it doesn't recognize.

---

## The multi-tool moat

`alkham` captures **Claude Code _and_ Aider** through one pluggable engine —
and adding a new tool touches *only* a parser module (Codex CLI and Cursor are
on the roadmap). One install, every AI terminal.

## Structure for free — but never forced

| Behavior | Toggle |
|---|---|
| Project routing | `features.routing` |
| Auto Map-of-Content | `features.auto_moc` |
| Frontmatter tags | `features.tagging` |
| YAML frontmatter | `features.frontmatter` |
| Output dialect | `output.flavor` = `obsidian` \| `plain` |

Every behavior is independently switchable, so `alkham` **fits your existing
knowledge base instead of overwriting it.**

## CLI at a glance

| Command | What it does |
|---|---|
| `alkham init` | First-run wizard (output dir, flavor, toggles) |
| `alkham watch` | Background daemon — auto-capture as sessions end |
| `alkham sync [-t FILE] [-n]` | Capture the latest (or a specific) session; `-n` dry-runs |
| `alkham backfill [--since DATE] [--project NAME]` | Batch-capture your history |
| `alkham config [--edit]` | Show or edit the config |
| `alkham moc --project NAME` | Rebuild a project's Map of Content |
| `alkham install-close-command` | Install the `/close` artifact-extraction prompt |

## Install

```bash
pip install alkham            # the CLI + library
pip install 'alkham[watch]'   # adds the background `alkham watch` daemon
```

Requires **Python 3.9+**. Tested on macOS, Linux, and Windows.

> ⚠️ **Security — transcripts are captured _verbatim_.** `alkham` does **not**
> redact. Never capture sessions containing live API keys, tokens, or other
> secrets — they'd be written into your notes as-is. (Path-traversal and
> Markdown/YAML-injection from hostile log content *are* sanitized, so a
> transcript can never corrupt your vault.)

## Learn more

- [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) — what it does, for whom, and how it feels to use
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — how it's built
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — including **how to add a parser** for a new tool

## License

MIT © Ali Alkhamees
