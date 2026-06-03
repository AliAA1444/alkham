# Contributing to alkham

Thanks for your interest! `alkham` is a library-first, local-first tool. The
golden rules: **pure core, thin shell**, and **every feature toggleable**.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
mypy src
pytest
```

CI must stay green on macOS, Linux, and Windows across Python 3.9–3.12, so keep
`from __future__ import annotations` at the top of every module.

## How to add a parser for a new tool

The parser seam is designed so a new source touches **only** the `parsers/`
package — nothing in `sync`, `routing`, `formatter`, `flavors`, or `moc`.

1. Add `src/alkham/parsers/<tool>.py` with a class satisfying
   `TranscriptParser`:
   - `source_name: str`
   - `can_parse(self, path: Path) -> bool`
   - `parse(self, path: Path) -> Session` (the most-recent session)
   - `parse_all(self, path: Path) -> list[Session]` (every session; one for
     single-session files)
   - Call `register(<Tool>Parser())` at module scope.
2. Add **one import line** to `parsers/__init__.py` so it self-registers.
3. Add `<tool>` to the config `sources` schema if it's discoverable by `sync`.
4. Add a fixture under `tests/fixtures/` and a `tests/test_parsers_<tool>.py`,
   including a `get_parser_for` disambiguation test.

Leave metadata you can't reliably extract as empty/`None` — never fake it.

## Pull requests

- Keep diffs small and focused.
- New behavior is gated by a config toggle when it touches the user's vault.
- `ruff`, `mypy --strict`, and `pytest` all pass.
