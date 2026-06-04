# Changelog

All notable changes to `alkham` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-06-04

### Added
- **`alkham watch`** — a background daemon (watchdog) that auto-captures each
  session the moment its transcript goes quiet. Race-safe by construction:
  debounce-on-stability + the parsers' malformed-line tolerance + idempotent
  writes mean a too-early partial capture is simply overwritten by the complete
  one. Install with the `watch` extra: `pip install 'alkham[watch]'`.
- **Parser-driven discovery** — each parser registers where its transcripts
  live, so `find_transcripts` is no longer hard-coded; adding a tool is now
  zero-core-change end-to-end (not just the parse step).

### Notes
- OpenAI Codex CLI and Cursor parsers are planned for v0.3.0 (pending real
  session samples to verify their on-disk formats).

## [0.1.0] — 2026-06-03

### Added
- Library-first parsing engine with a pluggable `TranscriptParser` seam and an
  import-populated registry (`get_parser_for` / `register`).
- **Claude Code** (`*.jsonl`) and **Aider** (`.aider.chat.history.md`) parsers —
  the multi-tool moat. The Aider parser splits the append-only history into
  per-session notes with stable, append-safe ids (idempotent re-sync).
- Vault-agnostic output: `obsidian` and `plain` flavors.
- Independently toggleable routing, Auto-MOC, tagging, and frontmatter.
- Security hardening for untrusted transcripts: path-traversal sanitization
  with a containment backstop, and `[[wikilink]]` / `![[embed]]` / YAML
  frontmatter injection neutralization.
- `alkham` CLI: `init`, `sync`, `backfill`, `config`, `moc`,
  `install-close-command`.
- CI across macOS, Linux, and Windows (Python 3.9–3.12); PyPI publishing via
  Trusted Publishing (OIDC).
