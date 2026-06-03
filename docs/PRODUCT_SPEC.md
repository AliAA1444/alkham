# Product Specification — `alkham`

> **Audience:** Anyone (human or AI) who needs to know exactly what `alkham`
> does, for whom, and how a user experiences it. This defines *what* to
> build; `ARCHITECTURE.md` defines *how*.

---

## 1. Problem statement

Developers increasingly work through AI coding CLIs (Claude Code, Aider,
Cursor's terminal, etc.). These sessions contain genuinely valuable
knowledge — architectural reasoning, working code, hard-won debugging
insights, decisions and their rationale. But that knowledge is trapped:

- It lives in raw JSONL/history files the developer never reads again.
- It's organized by session and timestamp, not by project or concept.
- It vanishes from working memory within days (and Claude Code auto-deletes
  transcripts after ~30 days).
- There's no path from "we figured this out in the terminal" to "this is
  part of how I think about this codebase."

The result: developers re-solve solved problems, forget why they made past
decisions, and lose the compounding value of their own work.

## 2. The solution and the wedge

`alkham` is a library + CLI that **captures AI coding sessions as readable
narratives** and files them into a Markdown knowledge base — turning a
disposable terminal log into a permanent, navigable record you'll actually
return to. Capture is a single `alkham sync` today; watch mode (Phase 7) makes
it automatic post-launch.

**The positioning wedge — say this precisely:** `alkham` performs
**frictionless, one-command capture of session narratives designed for
reading.** This is the distinction that separates it from the entire "AI
memory" category (mem0, Letta, Zep, Basic Memory, et al.). Those tools store
entity-relation triples or LLM-extracted preference bullets optimized for *an
AI to consume later*. `alkham` produces clean, chronological, human-legible
session notes optimized for *a person to read, search, and link*. The
defining axis of the wedge is **for reading** (not for LLM re-ingestion); the
second axis is **low-friction capture** — a single `alkham sync` with no
copy-paste-format work. v0.1.0 deliberately ships this manual one-command
form; *fully automatic* capture (the moment a session closes) is the Phase-7
`watch` evolution of the same wedge, **not** a v0.1.0 claim — so launch
messaging says "frictionless/one-command," never "automatic."

It runs locally, requires no API keys, no cloud, and no account, and it
works whether or not you use Obsidian.

## 3. Target user

- **Primary:** Individual developers who use an AI coding CLI *and* keep (or
  want to keep) a Markdown knowledge base. Comfortable in the terminal,
  opinionated about tools, allergic to friction and lock-in.
- **Secondary — non-Obsidian note-takers:** Developers who use VS Code +
  Markdown, Logseq, Notion (via Markdown import), or plain folders. `alkham`
  must serve them as a universal "AI terminal → Markdown" exporter, not
  force them into Obsidian.
- **Tertiary — library consumers:** Engineers and organizations who want to
  *parse* AI session logs programmatically (analytics, compliance, dataset
  curation) without the CLI at all.
- **Not targeting (yet):** Teams needing collaboration/multiplayer,
  non-technical users.

## 4. Core value propositions

1. **Zero-friction capture.** Knowledge gets saved with one command and no
   manual copy-paste-format work — and, post-launch (`watch` mode, Phase 7),
   without the developer thinking about it at all.
2. **Built for reading.** Output is a readable session narrative, not a data
   structure for machines — the wedge that distinguishes `alkham` from AI
   memory tools.
3. **Multi-tool from one binary.** Claude Code and Aider at launch (Cursor
   later) through one tool — the defensible moat no competitor offers.
4. **Structure for free, but never forced.** Notes can arrive routed to the
   right project, tagged, and linked into a graph — and every one of those
   behaviors can be turned off so `alkham` fits an existing system instead
   of overwriting it.
5. **Local and yours.** Plain Markdown in a location you own. No cloud, no
   account, no subscription, no lock-in.
6. **Signal over noise.** Actively filters triviality so the knowledge base
   stays valuable instead of becoming a junk drawer.

---

## 5. Feature specification

### 5.1 v0.1.0 features (the launch set)

**F1 — Zero-friction capture**
Parses a raw session transcript into a cleanly formatted, readable Markdown
note: optional YAML frontmatter, a readable header block, the conversation
rendered with clear human/assistant turns, and tool-use breadcrumbs (which
files were touched, which commands ran) without dumping verbose tool output.

**F2 — Multi-tool capture (Claude Code + Aider) — THE MOAT**
Captures both Claude Code (`~/.claude/projects/*.jsonl`) and Aider
(`.aider.chat.history.md` in project roots) through one tool and one
pluggable parser interface. This is the single capability no competitor
offers at launch and is the strategic centerpiece of v0.1.0. Aider is
cheap to support because it already emits Markdown — so the moat is
established at low cost on day one. **Asymmetry to set expectations:** Aider's
history carries less structured metadata than Claude Code's JSONL, so Aider
notes have reduced tool-use breadcrumbs (files touched / commands run);
unknowns are left empty rather than faked (see F1). The moat is *coverage* —
per-tool fidelity varies, and that is acceptable. Aider's history is also a
single append-only file holding many sessions, so the parser splits it into
per-session `Session` objects (see ARCHITECTURE / ROADMAP Phase 4).

**F3 — Dynamic project routing (toggleable)**
Reads the originating working directory and derives a project name, spawning
`<base>/10-Projects/<project>/sessions/` on demand and routing the note
there. A configurable, **case-insensitive blocklist** (`~`, `workspace`,
`Downloads`, `tmp`, etc.) catches non-project directories and routes them to
an inbox. **Can be disabled** (`features.routing: false`) so everything lands
in a single folder for users who don't want project subtrees.

**F4 — Noise-skipping titles**
Filenames come from the first *substantive* human prompt, skipping system
commands (`/clear`, `/model`, `/exit`). Clean human-readable slug plus a
6-character id slice to guarantee no collisions (critical during backfills).

**F5 — Zero-orphan graph / Auto-MOC (toggleable)**
Every captured note is linked into a per-project Map of Content (hub) so the
graph view has no orphans. **Fully disable-able** (`features.auto_moc:
false`) so it never disturbs a power user's existing MOC/linking structure,
and off by default for the `plain` flavor.

**F6 — Vault-agnostic output flavors**
An `output.flavor` setting (`obsidian` | `plain`) controls the Markdown
dialect. Obsidian users get wikilinks and tags; VS Code/Notion/plain-folder
users get portable Markdown. This is what makes `alkham` a *universal*
exporter rather than an Obsidian-only tool. (A `logseq` flavor is deferred
post-launch to protect the v0.1.0 timeline; the flavor seam makes it a
drop-in addition later with no core changes.)

**F7 — Configuration wizard (`alkham init`)**
Interactive first-run wizard: pick output location (**any directory**,
defaulting to a detected Obsidian vault if found but never requiring one),
pick a flavor, set known projects, and toggle features. Writes config to the
OS-correct directory. Eliminates every hardcoded path. Gating feature for a
public release.

**F8 — The library API**
`from alkham.parsers import get_parser_for` → `.parse()` → a typed `Session`.
A documented, tested, public Python API so `alkham` is usable as a
dependency, not just a command. Includes `docs/library-usage.md`.

**F9 — The closing routine (`/close`) (toggleable)**
A companion AI prompt (installed into the user's AI CLI) that extracts only
high-value artifacts — ADRs, reusable snippets, bug postmortems — while
skipping sessions that produced nothing worth keeping. Governed by
`features.artifact_extraction`. Runs inside the user's AI CLI, not inside
`alkham`; `alkham` provides and installs the prompt. **Scope:** v0.1.0
targets Claude Code's custom-command surface (`alkham install-close-command`);
Aider has no equivalent slash-command install, so `/close` is
Claude-Code-only at launch and the wizard says so.

**F10 — Backfill**
Batch-process historical sessions (`alkham backfill --since <date>` /
`--project <name>`) through the same pipeline, honoring the message
threshold.

### 5.2 Post-launch features

**F11 — Watch mode / daemon (`alkham watch`)** *(Phase 7)*
Background process that auto-syncs each session the moment it closes —
removing even the need to run `sync`. Handles the "still being written"
race; cleanly stoppable.

**F12 — Cursor support** *(Phase 8)*
A Cursor parser (reading `state.vscdb`) added via the same pluggable
interface with no core changes. Deferred because Cursor's schema changes
frequently and is a maintenance treadmill — taken on only once traction
justifies it.

---

## 6. User journeys

### Journey A — First-time setup (Obsidian user)
1. `pip install alkham`
2. `alkham init`
3. Wizard detects `~/Documents/Obsidian` and offers it; user accepts.
4. Wizard: flavor → `obsidian` (pre-selected because a vault was detected).
5. Wizard: feature toggles → user keeps defaults (all on).
6. Wizard: known projects → blank (auto-detect).
7. Config written. Prints: *"You're set. Run `alkham sync` after your next
   Claude Code or Aider session."* Offers to install the `/close` command.

### Journey A2 — First-time setup (non-Obsidian user)
1. `pip install alkham`
2. `alkham init`
3. No vault detected → wizard asks for any directory; user enters
   `~/notes` (a VS Code Markdown folder) or `~/logseq-graph`.
4. Wizard: flavor → user picks `plain` (Logseq users use `plain` too until the
   `logseq` flavor lands post-launch).
5. Wizard notes that Auto-MOC defaults off for `plain` and asks whether to
   enable routing; user keeps a single flat folder.
6. Config written. `alkham` now works as a universal AI-terminal → Markdown
   exporter for their non-Obsidian workflow.

### Journey B — The daily capture (manual)
1. Developer finishes a session (Claude Code or Aider) in `~/code/crowdflow`.
2. Runs `alkham sync`.
3. Output:
   ```
   ✓ Captured: "Add JWT refresh rotation"  [source: claude-code]
     Project: crowdflow → 10-Projects/crowdflow/sessions/
     Linked into crowdflow-MOC.md
   ```
4. Opens their editor; the note is there, readable, linked.

### Journey C — Daily capture (automatic, Phase 7)
1. `alkham watch` runs once (or as a login item).
2. Developer works across many projects, ending sessions naturally.
3. Each session is captured and routed automatically as it closes.

### Journey D — Backfilling history
1. New user has weeks of past Claude Code + Aider sessions.
2. `alkham backfill --since 2026-04-01`
3. Tool reports how many it found, processes each, skips trivial ones.

### Journey E — Power user protecting an existing vault
1. Developer already has a meticulously structured vault with their own MOC
   system and tag taxonomy.
2. `alkham config --edit` → sets `features.auto_moc: false`,
   `features.tagging: false`, `features.routing: true`.
3. `alkham` now drops clean, routed session notes into project folders
   **without** creating MOC files or injecting tags — fitting the existing
   structure instead of fighting it.

### Journey F — The library consumer (company / researcher)
1. `pip install alkham` inside a data pipeline.
2. ```python
   from alkham.parsers import get_parser_for
   session = get_parser_for("employee_chat_log.jsonl").parse()
   for m in session.messages:
       index(m)   # feed analytics / compliance / dataset tooling
   ```
3. No CLI, no config — just structured parsing of AI logs at scale.

---

## 7. CLI command surface (the contract)

| Command | Purpose |
|---|---|
| `alkham init` | First-run wizard; pick any output dir + flavor + toggles. |
| `alkham sync` | Capture the most recent session (Claude Code or Aider). |
| `alkham sync -t <file>` | Capture a specific transcript (any supported source). |
| `alkham sync -n` / `--dry-run` | Render to stdout without writing. |
| `alkham backfill --since <date>` | Batch-process historical sessions. |
| `alkham backfill --project <name>` | Backfill one project only. |
| `alkham watch` | *(Phase 7)* Daemon that auto-captures on session close. |
| `alkham config` | Print current config and its file path. |
| `alkham config --edit` | Open config in `$EDITOR`. |
| `alkham moc --project <name>` | Rebuild a project's MOC (if MOC enabled). |
| `alkham install-close-command` | Install the `/close` prompt into the AI CLI. |
| `alkham --version` | Print version. |
| `alkham --help` | Auto-generated help. |

---

## 8. Quality bar (definition of "good")

- **Never corrupts a knowledge base.** Idempotent, additive,
  collision-resistant. The trust foundation; violating it once loses a user.
- **Captures verbatim — secrets are the user's responsibility.** `alkham`
  does not redact; it writes transcript content as-is (a deliberate v0.1.0
  non-goal for speed). The `init` wizard and README warn loudly never to
  capture sessions containing live API keys or secrets. Path- and
  Markdown-injection sanitization still protect the vault from hostile
  content (ARCHITECTURE §5).
- **Never imposes unwanted structure.** Every toggle is honored exactly;
  with MOC/tagging/routing off, `alkham` writes only clean note files.
- **Never writes noise it was told to skip.** Blocklist, message threshold,
  and noise-skipping titles all hold. When `sync` finds only a sub-threshold
  session (below `min_messages`), it writes nothing and says so explicitly
  (e.g. *"Skipped: latest session has 2 messages (min 4) — nothing
  written."*) rather than failing silently.
- **Works without Obsidian.** `plain` flavor produces portable Markdown that
  opens correctly in VS Code, Logseq, or any editor.
- **Library two-liner works** exactly as documented and is covered by a test.
- **Clear failure.** Misconfiguration or an unparseable file → one-line
  actionable message, never a traceback.
- **Fast.** A single `sync` feels instant; backfill of hundreds completes in
  seconds.
- **Cross-platform paths** correct on macOS, Linux, Windows.

---

## 9. Success metrics (post-launch)

- A new user goes from `pip install` to first captured note in under two
  minutes — on Obsidian *or* a plain folder.
- Zero "it overwrote/corrupted my notes" reports.
- `alkham` covers Claude Code + Aider at launch — verified as the only tool
  doing so — and a Cursor parser can later be added touching only `parsers/`.
- The library API is adopted by at least one external project or used
  standalone (evidence the library-first bet paid off).
- Users report returning to the captured notes (navigating the graph,
  referencing `/close` artifacts later) — evidence the "for reading" wedge
  is real.

---

## 10. Strategic context (why this shape, why now)

The market analysis is explicit: the niche is real and growing, **not served
by any single tool**, and **being squeezed from above** by Anthropic's
`/export`, Obsidian's native CLI, and large Skills repos on a ~6–18 month
horizon. Three implications encoded into this spec:

1. **Speed and multi-tool breadth are the deciding factors** — so Aider is
   in v0.1.0 (F2), not deferred. Local-first and clean Markdown are *table
   stakes*, not the moat.
2. **The moat Anthropic cannot copy is multi-tool capture** — Anthropic owns
   only Claude Code. Every additional supported tool widens the gap.
3. **The "for reading, low-friction" wedge** (§2) is the defensible
   positioning against the funded AI-memory category, which complicates a
   naive "humans vs AIs" story but does not occupy the readable-narrative
   corner. v0.1.0 ships one-command capture; fully automatic `watch` capture
   is the Phase-7 evolution of the same wedge.
