# alkham

**Frictionless, one-command capture of your AI coding-CLI sessions — Claude
Code _and_ Aider — as readable Markdown notes.** Library-first; Obsidian by
default, but works with any Markdown folder.

> ⚠️ **Security — transcripts are captured _verbatim_.** `alkham` does **not**
> redact. Never capture sessions that contain live API keys, tokens, or other
> secrets: they will be written into your notes as-is. (Path-traversal and
> Markdown-injection are still sanitized so a log can't corrupt your vault.)
> See `docs/ARCHITECTURE.md` §10.

> **Status:** pre-alpha, under active construction toward `v0.1.0`. The CLI is
> still being scaffolded — see `docs/ROADMAP.md`.

## Quickstart (target UX)

```bash
pip install alkham
alkham init      # pick an output folder + flavor, toggle features
alkham sync      # capture your most recent Claude Code or Aider session
```

Capture is a single `alkham sync` today; automatic capture (`alkham watch`)
arrives post-launch.

## Use it as a library

```python
from alkham.parsers import get_parser_for

session = get_parser_for("chat_log.jsonl").parse()
print(session.messages)
```

## Documentation

- `docs/PRODUCT_SPEC.md` — what it does, for whom, and how it feels to use
- `docs/ARCHITECTURE.md` — how it's built (the technical source of truth)
- `docs/ROADMAP.md` — the phased build plan to `v0.1.0`

## License

MIT
