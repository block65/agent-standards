---
name: rust-book
description: >
  Agentic pipeline for generating idiomatic Rust architectural guides (like AGENTS.md, best-practices docs, or onboarding docs) by extracting knowledge from the official Rust Programming Language Book. Use this skill whenever the user wants to create Rust-specific guidance documents, AGENTS.md files for Rust repos, idiomatic Rust style guides, or any doc that should be grounded in official Rust best practices. Also use it when they ask to "distill the Rust book", "extract Rust patterns", or when they need to set up the rust-book knowledge base for a project. Trigger even if the user just says "write an AGENTS.md for my Rust project" — they almost certainly want this grounded in official Rust guidance.
---

# Rust Book Agentic Pipeline

This skill powers a two-phase system for producing high-quality, idiomatic Rust architectural guides. The knowledge base comes from the official [Rust Programming Language Book](https://doc.rust-lang.org/book/).

## Architecture Overview

- **Phase 1 (Build-time):** Run `distill.py` once to pre-process the Rust Book into dense, token-efficient chapter summaries.
- **Phase 2 (Run-time):** A Planner agent uses `get_table_of_contents` to identify relevant chapters, then an Implementation agent uses `fetch_distilled_chapters` to retrieve only the needed content and write the final guide.

### Paths — two kinds, don't confuse them

- **Shipped skill assets** (`scripts/distill.py`, `references/toc.md`) live inside this skill's own directory. Always address them as `${CLAUDE_PLUGIN_ROOT}/skills/rust-book/...` so the path resolves whether the skill is installed as a plugin or standalone. Do not look for them under a bare `~/.claude/skills/...` path, and do not go hunting for them with the Explore agent — they are exactly where `${CLAUDE_PLUGIN_ROOT}` says.
- **Generated distilled cache** (`distilled/`) is written once and shared across all projects, so it lives in a stable home location — `~/.claude/skills/rust-book/distilled/` — that survives plugin reinstalls/updates. This is the default `--out-dir` baked into `distill.py`.

---

## Phase 1: One-Time Setup — Distill the Rust Book

The distilled knowledge base lives at `~/.claude/skills/rust-book/distilled/` — shared across all projects, so you only do this once.

Check whether it has content:
```bash
ls ~/.claude/skills/rust-book/distilled/
```

If it's empty or missing, run the distiller against a local clone of the Rust Book:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/rust-book/scripts/distill.py" \
  --src-dir /path/to/rust-lang/book/src \
  --provider claude-cli   # or: gemini-cli, copilot-cli
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
2. Read each file
3. Concatenate with this header:

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

2. FETCH CONTENT — two paths, try in order:

   PATH A (distilled cache):
   - Check if ~/.claude/skills/rust-book/distilled/ has files matching <chapter_id>_*_distilled.md
   - If yes: read and concatenate them → use as source

   PATH B (live web fallback — use when distilled/ is empty or missing):
   - For each chapter ID, map to the URL slug using the table below
   - Fetch with WebFetch: https://doc.rust-lang.org/book/<slug>.html
   - Use the fetched content as source (it will be less dense than distilled, but still authoritative)

3. WRITE the final guide using the fetched content as the authoritative source.
```

### Chapter ID → URL Slug Mapping (for PATH B)

| Chapter ID | URL slug |
|------------|----------|
| ch01 | ch01-00-getting-started |
| ch02 | ch02-00-guessing-game-tutorial |
| ch03 | ch03-00-common-programming-concepts |
| ch04 | ch04-00-understanding-ownership |
| ch05 | ch05-00-structs |
| ch06 | ch06-00-enums |
| ch07 | ch07-00-managing-growing-projects |
| ch08 | ch08-00-common-collections |
| ch09 | ch09-00-error-handling |
| ch10 | ch10-00-generics |
| ch11 | ch11-00-testing |
| ch12 | ch12-00-an-io-project |
| ch13 | ch13-00-functional-features |
| ch14 | ch14-00-more-about-cargo |
| ch15 | ch15-00-smart-pointers |
| ch16 | ch16-00-concurrency |
| ch17 | ch17-00-async-await |
| ch18 | ch18-00-oop |
| ch19 | ch19-00-patterns |
| ch20 | ch20-00-advanced-features |
| ch21 | ch21-00-final-project-a-web-server |

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

**Want to re-distill a chapter:** Delete the specific file from `~/.claude/skills/rust-book/distilled/` and re-run the distiller with `--chapter ch09` to process only that chapter.
