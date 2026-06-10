---
name: rust-book
description: >
  Agentic pipeline for generating idiomatic Rust architectural guides (like AGENTS.md, best-practices docs, or onboarding docs) by extracting knowledge from the official Rust Programming Language Book. Use this skill whenever the user wants to create Rust-specific guidance documents, AGENTS.md files for Rust repos, idiomatic Rust style guides, or any doc that should be grounded in official Rust best practices. Also use it when they ask to "distill the Rust book", "extract Rust patterns", or when they need to set up the rust-book knowledge base for a project. Trigger even if the user just says "write an AGENTS.md for my Rust project" — they almost certainly want this grounded in official Rust guidance. Sources chapters from compend (compend get rust-book) when available, falling back to its own distill pipeline otherwise.
---

# Rust Book Agentic Pipeline

This skill powers a two-phase system for producing high-quality, idiomatic Rust architectural guides. The knowledge base comes from the official [Rust Programming Language Book](https://doc.rust-lang.org/book/).

## Content source: prefer compend when available

Check FIRST whether the `compend` command is on PATH and serves the book:

```bash
compend list   # look for rust-book
```

If it does, **use `compend get rust-book <topic>` as the fetch operation for
every chapter retrieval below** (topics are path-based and hyphenated:
`error-handling`, `smart-pointers`, `ownership`) and skip everything involving
`distill.py`. compend maintains a single version-pinned distilled cache shared
by all tools; running `distill.py` alongside it creates a second cache of the
same book that drifts from the first. The planner workflow is unchanged —
`references/toc.md` still drives chapter selection; only the retrieval command
differs. Fall back to the `distill.py` pipeline below only when compend is
absent or does not serve rust-book.

## Architecture Overview

The whole point of this skill is to **save context tokens**: the orchestrating agent should only ever see *distilled* chapters — never the full Rust Book text. Distillation always happens out-of-context (inside `distill.py`'s subprocess), so the raw chapter never enters the agent's window.

- **Distilled cache (the product):** dense, token-efficient chapter summaries in `distilled/`. Reading these is cheap.
- **Distill on read (cache miss):** when a needed chapter isn't cached, run `distill.py --from-github --chapter chNN`. It fetches the raw markdown from GitHub and compresses it *inside the subprocess*, writing the distilled file. Only that file enters context. The cache self-populates over time.
- **Phase 1 (optional pre-warm):** run `distill.py` once over the whole book to fill the cache up front instead of lazily. Not a prerequisite — the skill works cold, distilling chapters on demand.

> Do **not** WebFetch or Read raw chapters into the agent's context as a "fallback" — that pulls the full chapter into the window every time and defeats the entire purpose of the skill. Always go through `distill.py`.

### Paths — two kinds, don't confuse them

- **Shipped skill assets** (`scripts/distill.py`, `references/toc.md`) live inside this skill's own directory. Always address them as `${CLAUDE_PLUGIN_ROOT}/skills/rust-book/...` so the path resolves whether the skill is installed as a plugin or standalone. Do not look for them under a bare `~/.claude/skills/...` path, and do not go hunting for them with the Explore agent — they are exactly where `${CLAUDE_PLUGIN_ROOT}` says.
- **Generated distilled cache** (`distilled/`) is written once and shared across all projects, so it lives in a stable home location — `~/.claude/skills/rust-book/distilled/` — that survives plugin reinstalls/updates. This is the default `--out-dir` baked into `distill.py`.

---

## Phase 1: Optional Pre-Warm — Distill the Whole Book Up Front

This is **optional**. The skill distills chapters on demand (see Phase 2), so you can skip straight to generating guides. Pre-warming just fills the entire cache in one batch so later runs never pay the first-touch distill cost.

The distilled knowledge base lives at `~/.claude/skills/rust-book/distilled/` — shared across all projects, so you only do this once.

Check whether it has content:
```bash
ls ~/.claude/skills/rust-book/distilled/
```

To pre-warm everything straight from GitHub (no local clone needed):

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/rust-book/scripts/distill.py" \
  --from-github \
  --provider claude-cli   # or: gemini-cli, copilot-cli
```

Or distill from a local clone of the Rust Book if you have one:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/rust-book/scripts/distill.py" \
  --src-dir /path/to/rust-lang/book/src \
  --provider claude-cli
```

No API keys or pip installs required — uses whichever CLI tool you have set up.
The `--out-dir` defaults to `~/.claude/skills/rust-book/distilled/` automatically. See `--help` for all options.

---

## Phase 2: Generating the Guide

Once `~/.claude/skills/rust-book/distilled/` is populated, use the two runtime operations below.

### Operation 1: get_table_of_contents

**Purpose:** The Planner agent calls this to understand what the Rust Book covers, then decides which chapters are relevant to the user's request.

**How to execute:** Read the static ToC file:
```
${CLAUDE_PLUGIN_ROOT}/skills/rust-book/references/toc.md
```

This file lists all chapters with their IDs and one-sentence descriptions. Return it as text.

**Example Planner reasoning:**
> User wants a guide on error handling and async concurrency.
> ToC shows: ch09 = Error Handling, ch16 = Fearless Concurrency, ch17 = Async/Await.
> → Pass chapter_ids = ["ch09", "ch16", "ch17"] to the Implementation agent.

---

### Operation 2: fetch_distilled_chapters

**Purpose:** The Implementation agent retrieves the concentrated architectural rules for specific chapters.

**Inputs:** `chapter_ids` — a list like `["ch09", "ch16", "ch17"]`

**How to execute:**
1. For each chapter ID, locate the file in `~/.claude/skills/rust-book/distilled/` matching the pattern `<chapter_id>_*_distilled.md` (e.g., `ch09_error_handling_distilled.md`)
2. **On a cache miss** (no matching file), distill it on read — run, once per missing chapter:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/rust-book/scripts/distill.py" \
     --from-github --chapter <chapter_id> --provider claude-cli
   ```
   This fetches the raw markdown from GitHub and writes the distilled file to the cache **without the raw chapter ever entering your context**. Then re-resolve the file from step 1. Never WebFetch/Read the raw chapter into context instead.
3. Read each (now-present) file
4. Concatenate with this header:

```
---
The following are distilled architectural rules and syntax patterns extracted
from the Rust Programming Language Book chapters: {chapter_ids}.
Use these strictly to inform your output — do not invent patterns not present here.
---
```

**Return:** The full concatenated string as context for writing the guide.

---

## Agentic Workflow

Here is the canonical flow when a user asks for a Rust guide:

```
User: "Write an AGENTS.md for our Rust repo focusing on error handling and concurrency."

1. PLANNER:
   - Read ${CLAUDE_PLUGIN_ROOT}/skills/rust-book/references/toc.md
   - Identify relevant chapter IDs (e.g., ["ch09", "ch16"])

2. FETCH CONTENT (cache-first, distill-on-miss):
   - For each chapter ID, check ~/.claude/skills/rust-book/distilled/ for <chapter_id>_*_distilled.md
   - HIT  → read it
   - MISS → run `distill.py --from-github --chapter <chapter_id>` (compresses out-of-context), then read the file it wrote
   - Concatenate the distilled files → use as source

3. WRITE the final guide using the distilled content as the authoritative source.
```

Either way, only distilled text reaches your context — the raw book never does.

---

## Output Format for Rust Guides

When writing AGENTS.md or similar guides, structure the output as:

```markdown
# Rust Development Guide: [Topic]

> Generated from: Rust Book chapters [list]

## Core Rules
- [Actionable rules as bullet points]

## Standard Library Types
| Use Case | Type |
|----------|------|
| ...      | ...  |

## Canonical Patterns
\```rust
// Pattern: [name]
// [code example]
\```

## Anti-Patterns to Avoid
- [What NOT to do and why]
```

Keep the output dense and actionable — no narrative, no "getting started" fluff, just architecture.

---

## Troubleshooting

**Distiller fails to invoke the provider:** The distiller shells out to a local CLI (`claude`, `gemini`, or `copilot`) — no API keys. Confirm the chosen `--provider`'s CLI is installed and authenticated (e.g. run `claude -p hi` to check).

**`${CLAUDE_PLUGIN_ROOT}` is empty:** You're likely running outside the plugin runtime. Either invoke via the skill, or substitute the skill's real directory for `${CLAUDE_PLUGIN_ROOT}/skills/rust-book` in the commands above.

**Chapter file not found:** The distiller names files based on the source markdown filename. Run `ls ~/.claude/skills/rust-book/distilled/` to see available chapters and adjust chapter IDs accordingly.

**Want to re-distill a chapter:** Delete the specific file from `~/.claude/skills/rust-book/distilled/` and re-run the distiller with `--chapter ch09` (add `--from-github` if you have no local clone) to process only that chapter. Or pass `--overwrite`.

**Distill-on-read fails (no network / GitHub unreachable):** The chapter can't be distilled on demand. Report this rather than reading the raw chapter into context — pre-warm the cache later via Phase 1 when connectivity returns.
