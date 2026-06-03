# Changelog

All notable changes to `alkham` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

## [0.1.0] — unreleased
- Initial public release target: `pip install alkham` → `init` → `sync`
  produces a correct note, with the Claude Code + Aider moat already in place.
