# Roadmap — `alkham`

> **Audience:** The engineer (human or AI) building `alkham`, executing in
> order. Each phase has a clear goal, concrete tasks, and a definition of
> done. Build phases sequentially. Do not start a phase until the previous
> phase's "Definition of done" is met.

> **How to use this with Claude Code:** Work one phase at a time. Say
> "implement Phase N from ROADMAP.md" and have the agent complete and verify
> that phase before moving on. Do not build everything at once.

---

## Guiding sequencing principle

**Speed and multi-tool breadth are the moat.** The market analysis gives a
~6–18 month window before platform vendors absorb this niche. Therefore:
ship a real, installable `v0.1.0` *that already covers Claude Code AND
Aider* as fast as possible. Local-first and clean Markdown are table stakes,
not differentiators — do not over-invest in polish before the multi-tool
moat and the public library API are in users' hands. Phases 0–6 reach
`v0.1.0`. Phases 7–8 are post-launch.

**Key shift from earlier planning:** Aider support is pulled forward into
the launch path (Phase 4), not deferred. Cursor is explicitly pushed to
post-launch (Phase 8) because its `state.vscdb` schema is a maintenance
treadmill not worth carrying before traction.

---

## Phase 0 — Repository scaffolding

**Goal:** An empty but correctly structured, installable, importable project.

**Tasks:**
0. **Confirm the PyPI name `alkham` is available** (verified: `GET
   pypi.org/pypi/alkham/json` → 404) and **pin the GitHub `owner/repo`** now —
   Trusted Publishing (Phase 6) binds OIDC to an exact `owner/repo` + workflow
   filename.
1. Create the `src/alkham/` layout exactly as in `ARCHITECTURE.md` §4, with
   empty/stub modules (including `parsers/`, `flavors.py`). **Every module
   begins with `from __future__ import annotations`** so PEP-604 `X | None`
   annotations work on the Python 3.9 floor.
2. Write `pyproject.toml`: project metadata, name `alkham`,
   `requires-python = ">=3.9"`, runtime deps (`typer`, `rich`, `pyyaml`,
   `platformdirs`), `[project.scripts]` mapping `alkham = "alkham.cli:app"`,
   `[project.optional-dependencies] dev` (`pytest`, `pytest-cov`, `ruff`,
   `mypy`, `pre-commit`, `build`, `twine`) and `watch` (`watchdog`).
3. Add `ruff`, `mypy`, `pytest` config sections to `pyproject.toml`.
4. Minimal `cli.py` with a Typer app and a working `--version`.
5. `__init__.py` with `__version__ = "0.1.0"` and public re-exports stub;
   `__main__.py`.

**Definition of done:**
- `pip install -e ".[dev]"` succeeds.
- `alkham --version` prints `0.1.0`; `alkham --help` shows the app.
- `python -c "import alkham"` works (and, thanks to `from __future__ import
  annotations` in every module, imports on Python 3.9 too).
- `ruff check .` and `mypy src` pass on the stubs.

---

## Phase 1 — Models and the parser seam (the moat's foundation)

**Goal:** The shared data vocabulary and the extension point that makes
multi-tool support possible and the library API real.

**Tasks:**
1. Implement `models.py`: `Message`, `Session`, `RenderedNote` as frozen
   dataclasses per `ARCHITECTURE.md` §5.
2. Implement `parsers/base.py`: `TranscriptParser` Protocol (`can_parse`,
   `parse` → most-recent `Session`, `parse_all` → `list[Session]`), the
   registry, `register()`, and `get_parser_for()` returning a path-bound
   parser whose `.parse()` takes no argument and **raising
   `UnknownSourceError` (never `None`)** when nothing matches.
3. Re-export `get_parser_for` and `register` from `parsers/__init__.py` and
   from the top-level `alkham/__init__.py`. As each concrete parser lands
   (Phases 2 and 4), add its import to `parsers/__init__.py` so it
   self-registers on import (the registry is import-populated).
4. Implement `errors.py`: `AlkhamError` + `ConfigError`, `ParseError`,
   `RoutingError`, `UnknownSourceError(ParseError)`.

**Definition of done:**
- Models importable and instantiable.
- A dummy parser can register and be retrieved by `get_parser_for` in a test;
  `get_parser_for` on an unrecognized file raises `UnknownSourceError`.
- The documented import path `from alkham.parsers import get_parser_for`
  resolves.

---

## Phase 2 — The Claude Code parser

**Goal:** Turn a real Claude Code `.jsonl` transcript into a `Session`.

**Tasks:**
1. Implement `parsers/claude_code.py` satisfying `TranscriptParser`:
   - `can_parse()`: detect Claude Code JSONL (path under `.claude/projects`
     and/or line-schema sniff).
   - `parse()`: read line-by-line; extract human/assistant messages handling
     both string and content-block forms; collect `files_modified`,
     `commands_run`, `tools_used`; capture `model`, `started_at`,
     `ended_at`; decode `project`/`cwd` from the parent directory name.
   - Register the parser.
2. Add fixtures: `claude-basic.jsonl`, `claude-with-tools.jsonl`,
   `claude-noise-only.jsonl`.
3. `test_parsers_claude.py`: basic conversation, tool extraction, project
   decoding, noise-only transcript, malformed-line resilience.

**Definition of done:**
- Parsing each fixture yields a correct `Session`.
- Malformed lines are skipped without crashing.
- `get_parser_for("<a claude fixture>").parse()` returns the right `Session`.

---

## Phase 3 — Routing and titles (the pure core)

**Goal:** Decide *where* a session goes and *what* it's called — with
routing toggleable.

**Tasks:**
1. Implement `routing.py`: project extraction from `cwd`, blocklist,
   `resolve_output_dir(session, config)`. When `features.routing` is off,
   return the single configured output dir. Pure, no I/O. **Sanitize the
   decoded project/dir name** (strip `..`, path separators, leading `/`, and
   control chars; match the blocklist case-insensitively) and assert the
   resolved path stays under the configured base, else raise `RoutingError`.
2. Implement `titles.py`: skip system/noise commands, select first
   substantive human message, slugify, append 6-char id slice. Pure.
3. `test_routing.py` (known project → project dir; blocklisted cwd → inbox;
   routing-off → single dir; a hostile `cwd` containing `../` stays contained
   under the base; case-insensitive blocklist match) and `test_titles.py`
   (noise skipping; slug cleanliness; collision resistance).

**Definition of done:**
- Table-driven tests pass for all routing and title cases, including the
  routing-disabled and blocklist edge cases.

---

## Phase 4 — The Aider parser (THE MOAT — do not skip or defer)

**Goal:** Make `alkham` the only tool capturing Claude Code **and** Aider at
launch. This phase is the strategic core of v0.1.0.

**Tasks:**
1. Implement `parsers/aider.py` satisfying `TranscriptParser`:
   - `can_parse()`: recognize Aider's `.aider.chat.history.md` filename and
     content shape (it's Markdown, not JSONL).
   - `parse_all()`: **split the append-only `.aider.chat.history.md` into its
     constituent sessions** (Aider delimits them, e.g. `# aider chat started
     at <ts>` headers) and return **one `Session` per delimited chat**, not
     one blob. `parse()` returns the most-recent of those (what `sync` uses).
     For each session: parse its Markdown turns into `Message` objects; derive
     `project` from the directory containing the history file; `source =
     "aider"`; set a **per-session** `session_id` (hash of path + that
     session's start timestamp + ordinal) so re-runs are idempotent and a new
     appended session yields a new note; fill what's available (Aider gives
     less structured tool metadata than Claude — leave unknowns empty/None,
     don't fake).
   - Register the parser.
2. Add fixture `aider-history.md` reflecting Aider's real format, containing
   **multiple** chat sessions so splitting is exercised.
3. `test_parsers_aider.py`: multi-session **splitting** (N sessions → N
   `Session`s via `parse_all`; `parse` returns the latest; idempotent re-run;
   an appended session → a new note), message extraction, project derivation,
   and confirmation that `get_parser_for` routes an Aider file to this parser
   and a Claude file to the Claude parser (no cross-detection).

**Definition of done:**
- A multi-session Aider history file splits into the correct set of `Session`s
  via `parse_all()`; `parse()` returns the most recent; re-running is
  idempotent and a newly appended session yields a new note.
- `get_parser_for` disambiguates Aider vs Claude Code correctly.
- The same downstream pipeline (routing, titles) works unchanged on an Aider
  `Session` — proving the seam delivers the moat by touching only `parsers/`.

---

## Phase 5 — Formatter, flavors, and MOC (toggleable, vault-agnostic)

**Goal:** Render readable notes in multiple Markdown dialects; keep the graph
orphan-free when enabled; honor every toggle.

**Tasks:**
1. Implement `flavors.py`: `obsidian` | `plain` dialect rules (wikilinks/tags
   vs portable Markdown). (`logseq` deferred post-launch.)
2. Implement `formatter.py`: `Session` + `Config` + flavor → `RenderedNote`.
   YAML frontmatter only when `features.frontmatter` is on; tags only when
   `features.tagging` is on. Readable conversation body with tool breadcrumbs.
   Pure. **Escape/fence untrusted transcript content** so wikilinks/embeds/
   stray `---` blocks can't inject into the vault or break frontmatter; emit
   frontmatter via a safe YAML serializer.
3. Implement `moc.py`: create-or-update per-project MOC, idempotent. Skipped
   entirely when `features.auto_moc` is off; defaults off for `plain`.
4. `test_formatter.py` (frontmatter on/off, tagging on/off, body structure),
   `test_flavors.py` (both dialects render correctly; `plain` is
   Obsidian-free; an injection fixture with `[[...]]`/`---` is neutralized),
   `test_moc.py` (creates MOC; links note; re-link is no-op; fully skipped
   when disabled).

**Definition of done:**
- Notes render correctly in both flavors; `plain` contains no
  Obsidian-specific syntax.
- MOC linking is idempotent and produces zero orphans when on, and is a true
  no-op when off.
- Feature toggles for frontmatter and tagging are honored.

---

## Phase 6 — Config, wizard, orchestration, CLI, and v0.1.0 release

**Goal:** Compose everything, expose it, support Obsidian *and* non-Obsidian
users, and ship.

**Tasks:**
1. Implement `config.py`: `Config` frozen dataclass covering `output`
   (flavor + base_path + subdirs), `sources`, `features` toggles,
   `known_projects`, `blocklist`, `min_messages`; YAML load/save to
   `platformdirs.user_config_dir("alkham")/config.yaml`; `load_config()`
   raising `ConfigError` ("run `alkham init`") when absent.
2. Implement `run_init_wizard()` per Journeys A and A2 in `PRODUCT_SPEC.md`:
   - Detect an Obsidian vault; offer it but **never require it**.
   - Allow **any directory** as output base.
   - Prompt for flavor (`obsidian`/`plain`).
   - Prompt for feature toggles; explain Auto-MOC defaults off for `plain`.
   - Offer to install the `/close` command.
3. Implement `sync.py`: the linear pipeline (find → `get_parser_for` → parse
   → resolve_output_dir → format(flavor) → write → conditional MOC). **"Find"
   = scan all enabled sources** (Claude `*.jsonl` under `claude_projects_dir`;
   Aider `.aider.chat.history.md` under `aider_search_roots`) and pick the
   most recent by mtime; `-t <file>` bypasses the scan.
4. Implement `backfill.py`: discover transcript files since a date / by
   project across **all enabled sources**, expand each via the parser's
   `parse_all()` (so every Aider session in a history file is captured, not
   just the latest), run each `Session` through the sync pipeline, honor the
   message threshold.
5. Flesh out `cli.py`: `init`, `sync` (+ `-t`, `-n`), `backfill` (+ `--since`,
   `--project`), `config` (+ `--edit`), `moc --project`,
   `install-close-command`. Top-level handler catches `AlkhamError` → clean
   message + exit 1. Commands stay thin: load config, call library, render
   via `rich`.
6. `test_config.py` (round-trip; wizard writes valid config for both Obsidian
   and plain-folder paths; toggle persistence), `test_sync.py` (end-to-end
   against temp knowledge base + Claude and Aider fixtures, with a
   feature-toggle matrix), CLI smoke tests via Typer's `CliRunner`.
7. Author `docs/library-usage.md` (the public API, including the exact §1
   two-liner) and `docs/configuration.md` (full YAML schema + every toggle).
8. Repository polish:
   - `README.md`: badges (PyPI, CI, license, Python versions), 30-second
     pitch leading with **multi-tool capture** and the **for-reading** wedge
     (say "one-command/frictionless," not "automatic"), quickstart (`pip
     install alkham` → `init` → `sync`), a non-Obsidian usage note, a
     library-usage snippet, configuration summary, a **prominent security
     warning that transcripts are captured verbatim — never capture sessions
     with live API keys/secrets**, contributing pointer, demo GIF/asciinema
     if possible.
   - `LICENSE` (MIT), `.gitignore` (Python template + `config.yaml`),
     `CHANGELOG.md` (start at 0.1.0), `CONTRIBUTING.md` (incl. "how to add a
     parser"), `CODE_OF_CONDUCT.md` (Contributor Covenant).
   - `.github/workflows/ci.yml`: matrix macOS + Linux + **Windows**, Py
     3.9–3.12; runs `ruff check`, `mypy src`, `pytest`.
   - `.github/workflows/publish.yml`: build + publish to PyPI on `v*` tag via
     Trusted Publishing (OIDC, `id-token: write`, no stored token).
   - `.github/ISSUE_TEMPLATE/` bug + feature templates.
   - `.pre-commit-config.yaml` (ruff + hygiene hooks).
9. Configure PyPI Trusted Publishing **as a pending publisher *before* the
   first release** (a brand-new project has no "project settings" yet);
   specify the exact `owner/repo` + `publish.yml` workflow filename the OIDC
   trust expects. It converts to a normal project-settings publisher after the
   first publish.

**Definition of done:**
- Full pipeline works end-to-end on a real Claude Code transcript **and** a
  real Aider history file.
- `alkham init` produces valid config for both an Obsidian vault and a plain
  `~/notes` folder; the `plain` flavor output opens cleanly in VS Code.
- All feature toggles verified (routing off, MOC off, tagging off,
  frontmatter off).
- The documented library two-liner is covered by a passing test.
- CI green on all matrix cells.
- `git tag v0.1.0 && git push --tags` publishes to PyPI.
- `pip install alkham` on a clean machine → `init` → `sync` produces a
  correct note. **This is the v0.1.0 milestone — and it ships with the
  Claude Code + Aider moat already in place.**

---

## Phase 7 — Watch mode / daemon *(post-launch)*

**Goal:** Auto-capture on session close; eliminate manual `sync`.

**Tasks:**
1. Implement `watch.py` using `watchdog` (optional extra) monitoring the
   Claude Code projects dir and the Aider search roots.
2. Handle the "transcript still being written" race: debounce on file
   stability (no writes for N seconds) before syncing.
3. Cleanly startable/stoppable; print captures as they happen.
4. Document running it as a login item / `launchd` agent on macOS.
5. Tests for debounce logic and the watch→sync handoff.

**Definition of done:**
- `alkham watch` reliably captures sessions from both sources as they close,
  once each, with no duplicates and no partial-file reads.

---

## Phase 8 — Cursor support & further parsers *(post-launch)*

**Goal:** Widen the moat to Cursor and prove the seam with an outside-
contributable parser.

**Tasks:**
1. Implement `parsers/cursor.py` reading Cursor's `state.vscdb` (SQLite),
   satisfying `TranscriptParser`, self-registering via a one-line import in
   `parsers/__init__.py` — **no changes to core pipeline modules** (`sync`,
   `routing`, `formatter`, `flavors`, `moc`). Budget for schema churn; pin to
   known-good schema versions and fail gracefully on unknown ones.
2. Add `sources` selection so Cursor can be enabled/disabled in config.
3. Fixtures + `test_parsers_cursor.py`.
4. Document "how to contribute a new parser" in `CONTRIBUTING.md` and prove
   an external contributor can add one touching only `parsers/` + tests +
   config schema.

**Definition of done:**
- A Cursor session captures through the identical pipeline.
- Adding Cursor required touching only the `parsers/` package (new
  `parsers/cursor.py` **plus one self-registration import in
  `parsers/__init__.py`**), its tests, and the config `sources` schema —
  nothing in `sync.py`, `routing.py`, `formatter.py`, `flavors.py`, or
  `moc.py`. That contained blast radius is the proof the seam scales.

---

## Versioning & release discipline

- Semantic versioning. `0.x` while the API/CLI may still shift, but treat the
  `Session` dataclass and `get_parser_for` signature as stability
  commitments from v0.1.0 (additive changes only) since they are the public
  library contract.
- Every release: bump `version` in `pyproject.toml`, update `CHANGELOG.md`,
  commit, tag `vX.Y.Z`, push tag → CI publishes.
- Keep `main` always green and always installable.
