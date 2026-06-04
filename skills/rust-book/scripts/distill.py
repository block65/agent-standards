#!/usr/bin/env python3
"""
Rust Book Distiller — chapter → dense architectural rules.

Reads chapters either from a local rust-lang/book/src clone (--src-dir) or
straight from GitHub (--from-github), and distills each into dense
architectural rules using a local CLI tool. Output goes to a shared cache
directory for use by the rust-book skill's Phase 2 tools.

The GitHub mode powers "distill on read": when the skill hits a cache miss
for a chapter, it runs this script with --from-github --chapter chNN. The raw
markdown is fetched and compressed entirely inside this subprocess, so the
full chapter text never enters the calling agent's context — only the distilled
file does. That is the whole point of the skill: save context tokens.

Usage:
  python distill.py --src-dir /path/to/rust-lang/book/src      # local clone
  python distill.py --from-github --chapter ch09               # one chapter from GitHub
  python distill.py --from-github                              # whole book from GitHub

Providers (no API keys or pip installs required):
  claude-cli  — uses `claude` (Claude Code CLI)
  gemini-cli  — uses `gemini` (Gemini CLI)
  copilot-cli — uses `copilot` (GitHub Copilot CLI)
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_OUT_DIR = Path.home() / ".claude" / "skills" / "rust-book" / "distilled"

GITHUB_API = "https://api.github.com/repos/rust-lang/book/contents/src"
GITHUB_RAW = "https://raw.githubusercontent.com/rust-lang/book"

EXTRACTION_PROMPT = """\
You are a senior Rust architect. Read this chapter and extract ONLY the 'What' and 'How'. \
Strip away all narrative, tutorials, historical context, and the 'Why'. \
Output a dense Markdown list of actionable architectural rules, standard library types to use, \
and exact code snippets demonstrating the syntax. \
Be ruthlessly concise — every line must be directly useful to a developer writing production Rust code.\
"""

# CLI command templates. The chapter text is piped to stdin.
# {model} is substituted if --model is provided; omit the flag if not set.
CLI_COMMANDS = {
    "claude-cli": ["claude", "-p", EXTRACTION_PROMPT],
    "gemini-cli": ["gemini", EXTRACTION_PROMPT],
    "copilot-cli": ["copilot", EXTRACTION_PROMPT],
}

# Model flag to append when --model is specified
CLI_MODEL_FLAGS = {
    "claude-cli": ["--model", "{model}"],
    "gemini-cli": ["--model", "{model}"],
    "copilot-cli": [],  # copilot CLI may not support model selection
}


def run_cli(provider: str, model: str, text: str) -> str:
    cmd = list(CLI_COMMANDS[provider])

    if model:
        model_flags = [f.format(model=model) for f in CLI_MODEL_FLAGS[provider]]
        # Insert model flags before the prompt argument
        cmd = cmd[:-1] + model_flags + [cmd[-1]]

    full_input = f"{text}"
    result = subprocess.run(
        cmd,
        input=full_input,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        err = result.stderr.strip() or "(no stderr)"
        raise RuntimeError(f"{provider} exited {result.returncode}: {err}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError(f"{provider} returned empty output")

    return output


def get_chapter_slug(filename: str) -> str:
    """Convert 'ch09-01-unrecoverable-errors-with-panic.md' → 'ch09_unrecoverable_errors_with_panic'."""
    stem = Path(filename).stem
    match = re.match(r'^(ch\d+)', stem)
    prefix = match.group(1) if match else stem[:4]
    rest = re.sub(r'^ch\d+-?\d*-?', '', stem).replace('-', '_')
    return f"{prefix}_{rest}" if rest else prefix


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "rust-book-distiller"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _is_chapter_file(name: str) -> bool:
    """True for chapter source files; skips SUMMARY.md, appendices, non-chapters."""
    if not name.endswith(".md"):
        return False
    if name == "SUMMARY.md" or name.startswith("appendix"):
        return False
    return re.match(r'^ch\d+', name) is not None


def group_local_chapters(src_dir: Path) -> dict:
    """Map chapter_id → sorted list of filenames from a local src dir."""
    chapters = {}
    for md_file in sorted(src_dir.glob("*.md")):
        if not _is_chapter_file(md_file.name):
            continue
        chapter_id = re.match(r'^(ch\d+)', md_file.name).group(1)
        chapters.setdefault(chapter_id, []).append(md_file.name)
    return chapters


def group_github_chapters(ref: str) -> dict:
    """Map chapter_id → sorted list of filenames in rust-lang/book/src at `ref`."""
    listing = json.loads(_http_get(f"{GITHUB_API}?ref={ref}").decode("utf-8"))
    chapters = {}
    for entry in listing:
        name = entry.get("name", "")
        if not _is_chapter_file(name):
            continue
        chapter_id = re.match(r'^(ch\d+)', name).group(1)
        chapters.setdefault(chapter_id, []).append(name)
    for chapter_id in chapters:
        chapters[chapter_id].sort()
    return chapters


def main():
    parser = argparse.ArgumentParser(
        description="Distill the Rust Book chapters into dense architectural rule sets."
    )
    parser.add_argument(
        "--src-dir", default=None,
        help="Path to a local rust-lang/book/src/ directory (omit when using --from-github)"
    )
    parser.add_argument(
        "--from-github", action="store_true",
        help="Fetch chapter markdown straight from rust-lang/book on GitHub instead of a local clone"
    )
    parser.add_argument(
        "--ref", default="main",
        help="Git ref (branch/tag) to fetch from with --from-github (default: main)"
    )
    parser.add_argument(
        "--out-dir", default=str(DEFAULT_OUT_DIR),
        help=f"Output directory for distilled files (default: {DEFAULT_OUT_DIR})"
    )
    parser.add_argument(
        "--provider", default="claude-cli",
        choices=["claude-cli", "gemini-cli", "copilot-cli"],
        help="CLI tool to use (default: claude-cli)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Model name to pass to the CLI (optional; uses the CLI's own default if omitted)"
    )
    parser.add_argument(
        "--chapter", default=None,
        help="Process only this chapter ID (e.g., ch09). Omit to process all."
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds between CLI calls to avoid rate limiting (default: 2.0)"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-process chapters even if output file already exists"
    )
    args = parser.parse_args()

    if not args.from_github and not args.src_dir:
        print("Error: pass --src-dir <local book/src> or --from-github.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.from_github:
        source_label = f"github:rust-lang/book@{args.ref}/src"
        try:
            chapters = group_github_chapters(args.ref)
        except Exception as e:
            print(f"Error: could not list chapters from GitHub: {e}", file=sys.stderr)
            sys.exit(1)

        def read_chapter_text(name):
            return _http_get(f"{GITHUB_RAW}/{args.ref}/src/{name}").decode("utf-8")
    else:
        src_dir = Path(args.src_dir).expanduser().resolve()
        if not src_dir.exists():
            print(f"Error: --src-dir '{src_dir}' does not exist.", file=sys.stderr)
            sys.exit(1)
        source_label = str(src_dir)
        chapters = group_local_chapters(src_dir)

        def read_chapter_text(name):
            return (src_dir / name).read_text(encoding="utf-8")

    if args.chapter:
        chapter_id = args.chapter.lower()
        if chapter_id not in chapters:
            available = ", ".join(sorted(chapters.keys()))
            print(f"Error: chapter '{chapter_id}' not found. Available: {available}", file=sys.stderr)
            sys.exit(1)
        chapters = {chapter_id: chapters[chapter_id]}

    model_label = args.model or "(CLI default)"
    print(f"Provider: {args.provider} / Model: {model_label}")
    print(f"Source:   {source_label}")
    print(f"Output:   {out_dir}")
    print(f"Chapters: {len(chapters)}")
    print()

    processed = 0
    skipped = 0

    for chapter_id, names in sorted(chapters.items()):
        slug = get_chapter_slug(names[0])
        out_file = out_dir / f"{slug}_distilled.md"

        if out_file.exists() and not args.overwrite:
            print(f"  [skip] {out_file.name} (already exists; use --overwrite to reprocess)")
            skipped += 1
            continue

        try:
            combined = [read_chapter_text(n) for n in names]
        except Exception as e:
            print(f"  [error] {chapter_id}: could not read source: {e}", file=sys.stderr)
            continue
        chapter_text = "\n\n".join(combined)

        # Truncate to ~80k chars — leave headroom for the prompt in the CLI's context window
        if len(chapter_text) > 80_000:
            chapter_text = chapter_text[:80_000]
            chapter_text += "\n\n[TRUNCATED — chapter exceeded context limit]"

        print(f"  [distill] {chapter_id} → {out_file.name} ({len(chapter_text):,} chars input)")

        try:
            result = run_cli(args.provider, args.model, chapter_text)
        except Exception as e:
            print(f"  [error] {chapter_id}: {e}", file=sys.stderr)
            continue

        header = (
            f"# Distilled: {chapter_id.upper()}\n\n"
            f"> Source: {', '.join(names)}\n"
            f"> Provider: {args.provider} / {model_label}\n\n"
            f"---\n\n"
        )
        out_file.write_text(header + result, encoding="utf-8")
        print(f"  [done]   {out_file.name} ({len(result):,} chars output)")
        processed += 1

        if args.delay > 0 and processed < len(chapters):
            time.sleep(args.delay)

    print()
    print(f"Done. Processed: {processed}, Skipped: {skipped}")
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
