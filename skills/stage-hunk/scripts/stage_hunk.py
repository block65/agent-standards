#!/usr/bin/env python3
"""Stage or unstage specific hunks from a git diff without interactive prompts.

Usage:
    stage_hunk.py <file> <N> [N ...]
    stage_hunk.py --unstage <file> <N> [N ...]
    stage_hunk.py --list-hunks [--staged] <file>

Hunk indices are 1-based and match the order printed by --list-hunks, which
uses `git diff -U0` (the finest-grained split). Does not commit.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import NoReturn

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def usage() -> NoReturn:
    prog = "stage_hunk.py"
    print(f"Usage: {prog} <file> <N> [N ...]", file=sys.stderr)
    print(f"       {prog} --unstage <file> <N> [N ...]", file=sys.stderr)
    print(f"       {prog} --list-hunks [--staged] <file>", file=sys.stderr)
    sys.exit(1)


def git(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], input=stdin, capture_output=True, text=True
    )


def read_diff(file: str, *, staged: bool, context: int | None) -> str:
    args = ["diff"]
    if context is not None:
        args.append(f"-U{context}")
    if staged:
        args.append("--cached")
    args += ["--", file]
    result = git(*args)
    if result.returncode != 0:
        die(result.stderr.strip() or f"git diff failed for {file}")
    return result.stdout


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    section: str
    lines: list[str] = field(default_factory=list)


def parse_diff(diff: str) -> tuple[list[str], list[Hunk]]:
    """Split a single-file unified diff into (header_lines, hunks)."""
    header: list[str] = []
    hunks: list[Hunk] = []
    current: Hunk | None = None
    for line in diff.splitlines():
        m = HUNK_RE.match(line)
        if m:
            current = Hunk(
                old_start=int(m.group(1)),
                old_count=int(m.group(2)) if m.group(2) is not None else 1,
                new_start=int(m.group(3)),
                new_count=int(m.group(4)) if m.group(4) is not None else 1,
                section=m.group(5),
            )
            hunks.append(current)
        elif current is None:
            header.append(line)
        else:
            current.lines.append(line)
    return header, hunks


def in_ranges(line: int, ranges: list[tuple[int, int]]) -> bool:
    return any(lo <= line <= hi for lo, hi in ranges)


def resolve_selection(
    diff_u0: str, wanted: set[int]
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], int]:
    """Map wanted 1-based hunk indices (U0 numbering) to new-side ranges for
    modifications/additions and old-side ranges for pure deletions, which have
    no new-side line to match against. Geometry, not hunk identity — so it stays
    correct no matter how the U3 patch diff later merges these hunks."""
    _, hunks = parse_diff(diff_u0)
    new_ranges: list[tuple[int, int]] = []
    old_ranges: list[tuple[int, int]] = []
    for idx, h in enumerate(hunks, start=1):
        if idx not in wanted:
            continue
        if h.new_count == 0:
            old_ranges.append((h.old_start, h.old_start + h.old_count - 1))
        else:
            new_ranges.append((h.new_start, h.new_start + h.new_count - 1))
    return new_ranges, old_ranges, len(hunks)


def build_patch(
    diff: str,
    new_ranges: list[tuple[int, int]],
    old_ranges: list[tuple[int, int]],
    *,
    unstage: bool,
) -> str | None:
    """Rebuild a patch containing only the selected changes.

    Each emitted hunk derives its @@ header from its own coordinates — no cross-
    hunk state leaks. new_start differs by mode: when staging we apply selected
    hunks onto the index, so positions accumulate only emitted deltas; when
    unstaging the index frame is fixed, so each hunk keeps its original new_start.
    """
    header, hunks = parse_diff(diff)
    out: list[str] = []
    emitted_delta = 0  # net (new - old) lines from hunks emitted so far (stage)

    for h in hunks:
        filtered: list[str] = []
        has_selected = False
        prev_kept = True
        new_line, old_line = h.new_start, h.old_start

        for raw in h.lines:
            tag = raw[:1]
            if tag == " ":
                filtered.append(raw)
                prev_kept = True
                new_line += 1
                old_line += 1
            elif tag == "+":
                if in_ranges(new_line, new_ranges):
                    filtered.append(raw)
                    has_selected = True
                    prev_kept = True
                elif unstage:
                    # Addition we keep staged: it exists in the index, so it is
                    # context for this patch.
                    filtered.append(" " + raw[1:])
                    prev_kept = True
                else:
                    # Addition we are not staging: not in the index, so drop it.
                    prev_kept = False
                new_line += 1
            elif tag == "-":
                if in_ranges(new_line, new_ranges) or in_ranges(old_line, old_ranges):
                    filtered.append(raw)
                    has_selected = True
                    prev_kept = True
                elif unstage:
                    # Deletion we keep staged: its old content is gone from the
                    # index, so drop it from this patch.
                    prev_kept = False
                else:
                    # Deletion we are not staging: its old content is still in
                    # the index, so it is context.
                    filtered.append(" " + raw[1:])
                    prev_kept = True
                old_line += 1
            else:
                # "\ No newline at end of file" — only emit when the line it
                # attaches to was kept.
                if prev_kept:
                    filtered.append(raw)

        if not has_selected:
            continue

        old_count = sum(1 for l in filtered if l[:1] in (" ", "-"))
        new_count = sum(1 for l in filtered if l[:1] in (" ", "+"))
        new_start = h.new_start if unstage else h.old_start + emitted_delta
        out.append(f"@@ -{h.old_start},{old_count} +{new_start},{new_count} @@{h.section}")
        out.extend(filtered)
        if not unstage:
            emitted_delta += new_count - old_count

    if not out:
        return None
    return "\n".join(header + out) + "\n"


def apply_patch(patch: str, *, unstage: bool) -> bool:
    base = ["apply", "--cached"] + (["--reverse"] if unstage else [])
    for extra in ([], ["--whitespace=nowarn"]):
        if (
            git(*base, *extra, "--check", stdin=patch).returncode == 0
            and git(*base, *extra, stdin=patch).returncode == 0
        ):
            return True
    return False


def list_hunks(file: str, *, staged: bool) -> None:
    diff = read_diff(file, staged=staged, context=0)
    if not diff:
        die(f"no {'staged' if staged else 'unstaged'} changes in {file}")
    _, hunks = parse_diff(diff)
    for idx, h in enumerate(hunks, start=1):
        adds = dels = 0
        preview = ""
        for raw in h.lines:
            if raw[:1] == "+":
                adds += 1
                if not preview:
                    preview = raw[1:]
            elif raw[:1] == "-":
                dels += 1
                if not preview and adds == 0:
                    preview = raw[1:]
        if len(preview) > 80:
            preview = preview[:77] + "..."
        rng = f"{h.new_start}-{h.new_start + h.new_count - 1}"
        print(f'hunk {idx}: lines {rng:<8} ({dels} del, {adds} add, {dels + adds} lines) "{preview}"')


def stage(file: str, indices: list[str], *, unstage: bool) -> None:
    diff = read_diff(file, staged=unstage, context=None)
    if not diff:
        die(f"no {'staged' if unstage else 'unstaged'} changes in {file}")

    wanted = set()
    for arg in indices:
        if not re.fullmatch(r"\d+", arg):
            print(f"error: expected hunk index (integer), got: {arg}", file=sys.stderr)
            usage()
        wanted.add(int(arg))

    diff_u0 = read_diff(file, staged=unstage, context=0)
    new_ranges, old_ranges, total = resolve_selection(diff_u0, wanted)
    if not new_ranges and not old_ranges:
        die(f"no hunks matched indices {' '.join(indices)} (file has {total} hunks)")

    patch = build_patch(diff, new_ranges, old_ranges, unstage=unstage)
    if patch is None:
        die(f"no hunks matched indices {' '.join(indices)} in {file}")

    if not apply_patch(patch, unstage=unstage):
        print("error: generated patch failed to apply", file=sys.stderr)
        print("patch content:", file=sys.stderr)
        print(patch, file=sys.stderr)
        sys.exit(1)

    verb = "unstaged" if unstage else "staged"
    print(f"{verb} hunks {' '.join(indices)} from {file}")
    print(git("diff", "--cached", "--stat", "--", file).stdout, end="")


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--list-hunks":
        rest = argv[1:]
        staged = False
        if rest and rest[0] == "--staged":
            staged = True
            rest = rest[1:]
        if len(rest) != 1:
            usage()
        list_hunks(rest[0], staged=staged)
        return

    unstage = False
    if argv and argv[0] == "--unstage":
        unstage = True
        argv = argv[1:]
    if len(argv) < 2:
        usage()
    stage(argv[0], argv[1:], unstage=unstage)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"bug: stage-hunk crashed unexpectedly ({exc}) — please report this", file=sys.stderr)
        sys.exit(1)
