#!/usr/bin/env python3
"""
Rust Book Distiller — Phase 1 build-time script.

Reads chapters from a local rust-lang/book/src clone and distills each
into dense architectural rules using a local CLI tool. Outputs to a shared
cache directory for use by the rust-book skill's Phase 2 tools.

Usage:
  python distill.py --src-dir /path/to/rust-lang/book/src

Providers (no API keys or pip installs required):
  claude-cli  — uses `claude` (Claude Code CLI)
  gemini-cli  — uses `gemini` (Gemini CLI)
  copilot-cli — uses `copilot` (GitHub Copilot CLI)
"""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_OUT_DIR = Path.home() / ".claude" / "skills" / "rust-book" / "distilled"

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


def group_chapter_files(src_dir: Path) -> dict:
    """Group all .md files by chapter prefix (ch01, ch02, ...).

    Returns dict mapping chapter_id → sorted list of Path objects.
    Skips appendix and non-chapter files.
    """
    chapters = {}
    for md_file in sorted(src_dir.glob("*.md")):
        name = md_file.name
        if name == "SUMMARY.md" or name.startswith("appendix"):
            continue
        match = re.match(r'^(ch\d+)', name)
        if not match:
            continue
        chapter_id = match.group(1)
        chapters.setdefault(chapter_id, []).append(md_file)
    return chapters


def main():
    parser = argparse.ArgumentParser(
        description="Distill the Rust Book chapters into dense architectural rule sets."
    )
    parser.add_argument(
        "--src-dir", required=True,
        help="Path to a local rust-lang/book/src/ directory"
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

    src_dir = Path(args.src_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not src_dir.exists():
        print(f"Error: --src-dir '{src_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    chapters = group_chapter_files(src_dir)

    if args.chapter:
        chapter_id = args.chapter.lower()
        if chapter_id not in chapters:
            available = ", ".join(sorted(chapters.keys()))
            print(f"Error: chapter '{chapter_id}' not found. Available: {available}", file=sys.stderr)
            sys.exit(1)
        chapters = {chapter_id: chapters[chapter_id]}

    model_label = args.model or "(CLI default)"
    print(f"Provider: {args.provider} / Model: {model_label}")
    print(f"Source:   {src_dir}")
    print(f"Output:   {out_dir}")
    print(f"Chapters: {len(chapters)}")
    print()

    processed = 0
    skipped = 0

    for chapter_id, files in sorted(chapters.items()):
        first_name = files[0].name
        slug = get_chapter_slug(first_name)
        out_file = out_dir / f"{slug}_distilled.md"

        if out_file.exists() and not args.overwrite:
            print(f"  [skip] {out_file.name} (already exists; use --overwrite to reprocess)")
            skipped += 1
            continue

        combined = [f.read_text(encoding="utf-8") for f in files]
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
            f"> Source: {', '.join(f.name for f in files)}\n"
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
