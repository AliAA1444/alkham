# Architecture — `alkham`

> **Audience:** Engineers (human or AI) building or extending `alkham`.
> This document is the technical source of truth. If code and this doc
> disagree, treat it as a bug in one of them and reconcile.

---

## 1. What `alkham` is

`alkham` is **a Python library first, and a command-line tool second.** Its
core is a clean, importable engine that parses AI coding-CLI session
transcripts (Claude Code, Aider, and more) into structured, typed Python
objects. On top of that engine sits a CLI that captures those sessions and
files them into a Markdown knowledge base — an Obsidian vault by default,
but **any directory**, degrading gracefully into a universal "AI terminal →
Markdown" exporter for users of VS Code, Logseq, Notion, or plain folders.

It is a **local, offline, single-user** tool in its CLI form. No network
calls, no telemetry, no external APIs in the core capture path. Everything
runs on the user's machine against files already on disk.

### Why library-first matters

The CLI is one consumer of the engine. The engine is independently valuable:

- A company can point it at exported employee AI logs and get structured
  `Session` objects for analytics, compliance, or training-data curation —
  in a few lines, with no CLI involved.
- Researchers can batch-parse thousands of transcripts into a dataframe.
- Other tools (Obsidian plugins, web dashboards, MCP servers) can depend on
  `alkham` as a parsing dependency rather than reimplementing brittle JSONL
  handling.

This is a deliberate moat decision: the market analysis identifies the
**pluggable multi-tool parser** as `alkham`'s single most defensible asset.
By exposing it as a first-class library API — not buried inside CLI code —
we make it reusable, testable, and adoptable by downstream projects, which
compounds the moat.

The library API is intentionally trivial to call:

```python
from alkham.parsers import get_parser_for
# alkham does the heavy lifting to parse JSONL in one second!
session = get_parser_for("chat_log.jsonl").parse()
print(session.messages)
```

That two-line ergonomics target is a hard design constraint, not an
aspiration. `get_parser_for` auto-detects the source tool and returns a
parser bound to the path, so `.parse()` needs no argument and returns a
fully-populated `Session`. On an unrecognized file it **raises**
`UnknownSourceError` (it never returns `None`), so the two-liner is always
either a valid `Session` or a clean, catchable error — never an
`AttributeError`. Everything else in the engine serves making those two
lines correct and fast — see §5.

---

## 2. Design principles

These constrain every decision below.

1. **Library first, CLI second.** Every capability exists as a pure,
   importable function or class with a documented signature. The CLI is a
   thin orchestrator over the library. If a feature can only be reached
   through the CLI, that's a design bug.
2. **Pure core, thin shell.** All logic lives in pure functions that take
   inputs and return outputs with no side effects. I/O happens at the edges.
   This makes the core fully testable without invoking the CLI or touching
   the real filesystem.
3. **Configuration over hardcoding.** No path, project name, threshold, or
   feature flag is ever hardcoded in logic. Everything the user might change
   lives in a config file with sane defaults.
4. **Every feature is toggleable.** Power users have existing Second Brains
   with their own conventions. Auto-MOC, tagging, artifact extraction, and
   routing must each be independently disable-able so `alkham` never imposes
   structure on a knowledge base that doesn't want it.
5. **Vault-agnostic output.** Obsidian is the default target, not a
   requirement. The output layer degrades to plain Markdown in any
   directory. Obsidian-specific features (wikilinks, MOC) are a configurable
   *flavor*, not a hard dependency.
6. **Idempotent and non-destructive.** Running `alkham` twice must never
   corrupt the knowledge base or silently overwrite a user's notes. Captures
   are additive; filenames are collision-resistant.
7. **Fail loud, fail safe.** On any ambiguity, stop with a clear, actionable
   message rather than guessing and writing garbage.
8. **Extensible by interface, not by `if`-ladder.** Supporting a new AI tool
   means adding a parser module that satisfies an interface — never editing
   a growing chain of conditionals in the core.

---

## 3. Technology choices

| Concern | Choice | Why |
|---|---|---|
| Packaging / build | `pyproject.toml` + `hatchling` | Single source of truth for metadata and build. `setup.py`/`setup.cfg` are legacy. Hatchling is the modern, zero-config PEP 517 backend. |
| Layout | strict `src/` layout | Prevents tests from importing the local working tree instead of the installed package. Forces editable install during dev, so tests exercise the real package. |
| CLI framework | `Typer` | Type-hint-driven; generates `--help`, shell completion, colored output with minimal boilerplate. Built on Click. Ideal for a multi-command tool. |
| Terminal output | `rich` | Tables, colored status, the wizard UI. Typer integrates natively. |
| Config location | `platformdirs` | Resolves the OS-correct config directory across macOS/Linux/Windows. |
| Config format | YAML via `PyYAML` | Human-readable and hand-editable, which matters for a power-user dev tool. |
| Testing | `pytest` + `pytest-cov` | Standard. Fixtures make temp-vault testing trivial. |
| Lint + format | `ruff` | One fast tool replacing flake8 + isort + black. |
| Type checking | `mypy` | Catches interface drift — essential for the public library API and the parser abstraction. |

The library's only hard runtime dependencies are `pyyaml` and
`platformdirs`. `typer` and `rich` are used by the CLI. Watch mode's
`watchdog` is an optional extra. This keeps the library lightweight for
downstream importers who want parsing without the CLI surface.

---

## 4. Folder structure

```
alkham/
├── src/
│   └── alkham/
│       ├── __init__.py          # __version__, public API re-exports
│       ├── __main__.py          # `python -m alkham` entrypoint
│       ├── cli.py               # Typer app — command definitions only
│       ├── config.py            # Config dataclass, load/save, init wizard
│       ├── models.py            # Shared dataclasses (Session, Message, Artifact)
│       ├── parsers/
│       │   ├── __init__.py      # re-exports get_parser_for, register
│       │   ├── base.py          # TranscriptParser Protocol + registry
│       │   ├── claude_code.py   # Claude Code JSONL parser
│       │   └── aider.py         # Aider history parser (v0.1.0 — the moat)
│       ├── routing.py           # cwd→project extraction, blocklist, dir resolution
│       ├── titles.py            # noise-skipping title + slug + UUID suffix
│       ├── formatter.py         # Session → Markdown (+ vault flavor)
│       ├── flavors.py           # output flavor: obsidian | plain
│       ├── moc.py               # Map-of-Content create/update (toggleable)
│       ├── sync.py              # Orchestration: parse→route→format→write→MOC
│       ├── backfill.py          # Historical session discovery + batch sync
│       ├── watch.py             # (Phase 7) filesystem watcher / daemon
│       └── errors.py            # Typed exceptions
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── claude-basic.jsonl
│   │   ├── claude-with-tools.jsonl
│   │   ├── claude-noise-only.jsonl
│   │   └── aider-history.md
│   ├── test_routing.py
│   ├── test_titles.py
│   ├── test_parsers_claude.py
│   ├── test_parsers_aider.py
│   ├── test_formatter.py
│   ├── test_flavors.py
│   ├── test_moc.py
│   ├── test_config.py
│   └── test_sync.py
├── docs/
│   ├── ARCHITECTURE.md          # this file
│   ├── PRODUCT_SPEC.md
│   ├── ROADMAP.md
│   ├── library-usage.md         # how to use alkham as a Python dependency
│   └── configuration.md
├── .github/
│   ├── workflows/{ci.yml,publish.yml}
│   └── ISSUE_TEMPLATE/{bug_report.md,feature_request.md}
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── .gitignore
```

---

## 5. Module responsibilities

### `models.py` — the shared vocabulary
Defines the dataclasses every module passes around — the contract between
layers, and the **public return type of the library API**. Keep them dumb
(data only). Because `Session` is what library consumers receive, its shape
is a stability commitment: additive changes only after v0.1.0. `frozen=True`
gives *shallow* immutability only — the `messages`/`files_modified`/
`tools_used` containers are still mutable and `Session` is unhashable; treat
them as read-only by convention. **Every module begins with `from __future__
import annotations`**, so the `str | None` / `list[...]` annotations below
are lazy strings and the package imports cleanly on Python 3.9 (where PEP-604
unions would otherwise fail at class-definition time).

```python
@dataclass(frozen=True)
class Message:
    role: str            # "human" | "assistant"
    content: str
    timestamp: str | None

@dataclass(frozen=True)
class Session:
    session_id: str          # stable id (UUID from filename, or hash for Aider)
    source: str              # "claude-code" | "aider" | ...
    project: str             # decoded from cwd / transcript path
    cwd: str | None          # raw originating directory (may be unknown for Aider)
    messages: list[Message]
    files_modified: list[str]
    commands_run: list[str]
    tools_used: dict[str, int]
    started_at: str | None
    ended_at: str | None
    model: str | None

@dataclass(frozen=True)
class RenderedNote:
    filename: str
    markdown: str
    project: str
```

### `parsers/base.py` — the extension seam (the moat)
The single most important architectural element. Defines a `Protocol` every
parser satisfies, plus a registry so new parsers self-register by source
name. This is what makes `get_parser_for("file.jsonl")` work and what makes
adding Cursor later a zero-core-change operation.

```python
from typing import Protocol, runtime_checkable
from pathlib import Path
from alkham.models import Session

@runtime_checkable
class TranscriptParser(Protocol):
    source_name: str
    def can_parse(self, path: Path) -> bool: ...
    def parse(self, path: Path) -> Session: ...            # most recent session in the file
    def parse_all(self, path: Path) -> list[Session]: ...  # every session (backfill); Claude→1, Aider→N

_REGISTRY: dict[str, TranscriptParser] = {}

def register(parser: TranscriptParser) -> None:
    _REGISTRY[parser.source_name] = parser

def get_parser_for(path: str | Path) -> "BoundParser":
    """Auto-detect and return a parser bound to this transcript file.

    This is the primary public library entrypoint. The returned object's
    .parse() takes no argument — the path is already bound — so the
    documented two-liner works:

        session = get_parser_for("chat_log.jsonl").parse()

    Raises UnknownSourceError if no registered parser recognizes the file
    (it never returns None), so the documented two-liner is always either a
    Session or a clean, typed error.
    """
    p = Path(path)
    for parser in _REGISTRY.values():
        if parser.can_parse(p):
            return _bind(parser, p)
    raise UnknownSourceError(f"No registered parser recognizes {p}")
```

`__init__.py` re-exports `get_parser_for` and `register` at the top level
(`from alkham.parsers import get_parser_for`) so the public usage works
exactly as documented in §1, **and it imports each concrete parser module
(`claude_code`, `aider`, …) so they self-register on import** — without that
the registry would be empty and `get_parser_for` would recognize nothing. A
thin `BoundParser` wrapper closes over the path so consumers call `.parse()`
with no argument; because the bound wrapper's `.parse()` differs from the
Protocol's `parse(self, path)`, treat `TranscriptParser` as a structural
contract for parser *authors*, not an `isinstance` gate (`runtime_checkable`
only checks method names, not signatures).

**On "zero core changes":** adding a new tool (e.g. Cursor, ROADMAP Phase 8)
means adding a `parsers/<tool>.py` plus one import line in
`parsers/__init__.py` — i.e. touching **only** the `parsers/` package (plus
its tests and the config `sources` schema). Nothing in `sync`, `routing`,
`formatter`, `flavors`, or `moc` changes. That contained blast radius — not a
literal zero-line diff — is what "the seam scales" means here.

### `parsers/claude_code.py` — the first parser
Implements `TranscriptParser` for Claude Code JSONL. Owns all
Claude-specific knowledge: `type` field values, content-block structure,
tool-use extraction, project decoding from the `~/.claude/projects/`
directory name. Nothing else in the codebase knows Claude's format. Each
JSONL file is a single session, so `parse_all()` returns `[parse()]`.

### `parsers/aider.py` — the moat parser (v0.1.0)
Implements `TranscriptParser` for Aider. Aider writes
`.aider.chat.history.md` to the project root natively, so this parser reads
**Markdown, not JSONL** — which is exactly why it's cheap to add and why it
makes `alkham` the only tool covering Claude Code + Aider at launch. **The
history file is append-only and holds many sessions,** so the parser splits
it on Aider's session delimiters: `parse()` returns the most-recent session
(what `sync` captures) and `parse_all()` returns every session with a stable
per-session `session_id` (what `backfill` uses), so re-runs are idempotent and
newly appended sessions become new notes. Project name derives from the
directory containing the history file. `can_parse` recognizes the Aider
history filename/format. This parser is the strategic centerpiece of v0.1.0;
see ROADMAP Phase 4.

### `routing.py` — where a session belongs
Pure functions: decode project name from `cwd`, apply the blocklist
(case-insensitively), resolve the output directory. Given a `Session` and a
`Config`, returns a `Path`. No I/O. **Because `cwd`/project are derived from
possibly-untrusted transcript content, the decoded name is sanitized** — path
separators, `..`, leading `/`, and control characters are stripped or
rejected, and the resolved path is asserted to remain under the configured
base (raising `RoutingError` otherwise) — so a hostile log can never escape
the vault. When `features.routing` is off, everything goes to a single
configured directory.

### `titles.py` — human-readable identity
Pure functions: pick the first substantive human message (skipping `/clear`,
`/model`, `/exit`, etc.), slugify, append a 6-char id slice. Returns the
filename stem.

### `formatter.py` + `flavors.py` — Session → Markdown
`formatter.py` builds the note body and frontmatter from a `Session` +
`Config`. `flavors.py` controls *dialect*: `obsidian` (wikilinks, tags
suited to Obsidian) and `plain` (portable Markdown for VS Code/Notion/any
folder). The flavor is a config value, so the same engine serves Obsidian and
non-Obsidian users without branching logic scattered through the code.
(`logseq` is deferred post-launch; v0.1.0 ships `obsidian` + `plain` only.)
Both modules are pure. Frontmatter emission is itself gated by
`features.frontmatter`. **Transcript content is untrusted:** the formatter
fences/escapes message bodies so embedded `[[wikilinks]]`, `![[embeds]]`, or
a stray `---`/YAML block cannot inject into the vault graph or break the
note's own frontmatter, which is written via a safe YAML serializer.

### `moc.py` — the zero-orphan guarantee (toggleable)
Splits into a **pure** `plan_moc_update(existing_moc_text, note, config) ->
str | None` (computes the new MOC content, or `None` if the note is already
linked — this is the idempotency logic, unit-tested with no filesystem) and
a **thin** I/O wrapper `ensure_linked(note, config)` that reads the MOC file,
calls the pure planner, and writes only when it changed. Idempotent. **Fully
disable-able** via `features.auto_moc: false` — when off, `alkham` never
creates or edits MOC files, so it won't disturb a power user's existing
structure. Also defaults off for the `plain` flavor unless explicitly
enabled.

### `sync.py` — the orchestrator
The one place that composes the pipeline: `find transcript →
get_parser_for → parse → resolve_output_dir → format(flavor) → write file →
(if enabled) update MOC`. What the `sync` command calls. Linear and
readable.

### `config.py` — user reality
The `Config` dataclass, YAML load/save, and the `init` wizard. Exposes
`load_config()` (raises `ConfigError` with a "run `alkham init`" message if
absent) and `run_init_wizard()`. Owns the feature-toggle and flavor schema.

### `cli.py` — the thin shell
Typer command definitions. Each command: load config, call the relevant
library function, render output via `rich`. **No business logic here.**

### `errors.py` — typed failures
`AlkhamError` base, with `ConfigError`, `ParseError`, `RoutingError`, and
`UnknownSourceError(ParseError)` (raised by `get_parser_for` when no parser
matches a file). The CLI catches these at the top level and renders clean
messages with nonzero exit codes. Library consumers catch the same typed
exceptions.

---

## 6. Data flow (the `sync` path)

```
  transcript file (Claude Code JSONL  OR  Aider .aider.chat.history.md)
              │
              ▼
   parsers.get_parser_for(path)         ← auto-detects source via can_parse()
              │
              ▼
        parser.parse() ────────────────▶  Session  (models.py)
              │
              ▼
   routing.resolve_output_dir(session, config)
              │      routing ON  → 10-Projects/<proj>/sessions/ (or inbox via blocklist)
              │      routing OFF → single configured output dir
              ▼
   titles.make_filename(session) ─────▶  "2026-05-14_add-jwt-auth_a1b2c3.md"
              │
              ▼
   formatter.render(session, config, flavor) ─▶ RenderedNote
              │      flavor = obsidian | plain
              ▼
        write file to output dir
              │
              ▼
   if config.features.auto_moc:
       moc.ensure_linked(note, config) ─▶ updates <proj>-MOC.md (zero orphans)
   else:
       skip — never touches MOC files
```

Every arrow except the file-writes is a pure function. The entire
decision-making path is testable with in-memory `Session` objects and a
`Config` pointed at `tmp_path`.

---

## 7. Configuration model

Config lives at `platformdirs.user_config_dir("alkham")/config.yaml`.

```yaml
# ── Output target (vault-agnostic) ──────────────────────────
output:
  flavor: obsidian            # obsidian | plain   (logseq deferred post-launch)
  base_path: /Users/ali/Documents/Obsidian
  projects_subdir: "10-Projects"      # used only when routing is on
  inbox_subdir: "00-Inbox/unsorted"   # used only when routing is on

# ── Sources (the multi-tool moat) ──────────────────────────
sources:
  - claude-code
  - aider
claude_projects_dir: /Users/ali/.claude/projects
aider_search_roots:                   # where to look for .aider.chat.history.md
  - /Users/ali/code

# ── Feature toggles (power-user friendly) ──────────────────
features:
  routing: true               # false → everything to one folder
  auto_moc: true              # false → never create/edit MOC files
  tagging: true               # false → no auto tags in frontmatter
  artifact_extraction: true   # governs /close command behavior
  frontmatter: true           # false → bare Markdown, no YAML block

# ── Behavior ───────────────────────────────────────────────
known_projects: []            # empty = auto-detect from cwd
blocklist:                    # matched case-insensitively against the cwd basename
  - ""                        # guards against an empty / undecodable project name
  - home
  - workspace
  - downloads
  - tmp
  - scratch
min_messages: 4
```

`Config` is a **nested** frozen dataclass — `Config.output` (an
`OutputConfig`), `Config.features` (a `FeatureFlags`), etc. — so attribute
access like `config.features.auto_moc` and `config.output.flavor` is typed
rather than dict lookups. It is passed explicitly into every function that
needs it (dependency injection) — no module reaches for a global. The
`features` block is the contract behind design principle #4: each flag gates
a discrete capability so the tool adapts to an existing knowledge base rather
than overwriting its conventions. The `output.flavor` field is the contract
behind principle #5: non-Obsidian users select `plain` and get portable
output.

---

## 8. Error handling contract

- Library/pure functions raise typed exceptions from `errors.py`; they never
  call `sys.exit` or print. This is essential because library consumers need
  to catch, not have the process killed.
- `cli.py` wraps command bodies in a top-level handler that catches
  `AlkhamError`, prints a red one-line message via `rich`, exits code 1.
  Unexpected exceptions get a "this is a bug, please report" message.
- The knowledge base is never left half-written: render fully in memory,
  then write. MOC update happens after the note write succeeds.

---

## 9. Testing strategy

- **Library API** (`get_parser_for`, both parsers, `Session` shape) gets the
  most rigorous coverage — it's the public contract and the moat. Include a
  test that runs the exact documented two-liner from §1 against a real
  fixture path (asserting a populated `Session`), plus a test that
  `get_parser_for` on an unrecognized file raises `UnknownSourceError`.
- **Pure modules** (`routing`, `titles`, `formatter`, `flavors`) get
  exhaustive table-driven unit tests.
- **`sync` and `moc`** get integration tests against a `tmp_path` knowledge
  base and fixtures, including **feature-toggle matrices** (routing off, MOC
  off, plain flavor, frontmatter off).
- **CLI** gets smoke tests via Typer's `CliRunner`.
- Fixtures cover the tricky cases: system-noise-only sessions, heavy tool
  use, blocklisted directories, multi-turn code sessions, and an Aider
  history file.
- CI runs on macOS, Linux, **and Windows** across Python 3.9–3.12. Cross-OS
  is non-negotiable: the tool is path-heavy and the §8 quality bar promises
  correct Windows paths, so Windows must be in the matrix, not just claimed.

---

## 10. Explicit non-goals (for now)

- No cloud sync, no hosted service, no account system in the OSS core.
- No editing/round-tripping notes back into transcripts — capture is
  one-directional.
- No AI summarization in the core capture path (the `/close` prompt runs
  inside the user's own AI CLI). Keeps the tool free, offline,
  dependency-light.
- **No secret redaction.** `alkham` writes transcript content **verbatim**;
  it does not scan for or strip API keys, tokens, or other secrets. This is a
  deliberate v0.1.0 non-goal for speed — the `init` wizard and README warn
  loudly that users must not capture sessions containing live secrets.
  (Path-traversal and Markdown-injection sanitization, by contrast, *are*
  enforced — see `routing.py`/`formatter.py` in §5 — because they protect the
  "never corrupt a vault" guarantee.)
- No GUI. `alkham` is a library + CLI; the "UI" is the user's editor.
- Cursor support is explicitly deferred to post-launch (Phase 8): its
  `state.vscdb` schema changes frequently and is a maintenance treadmill not
  worth carrying before traction.
