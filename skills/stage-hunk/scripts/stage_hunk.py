#!/usr/bin/env python3
"""Stage or unstage specific hunks or lines from a git diff without interactive prompts.

Usage:
    stage_hunk.py <file> <N|N-M> [...]
    stage_hunk.py --lines <file> <N|N-M> [...]
    stage_hunk.py --unstage [--lines] <file> <N|N-M> [...]
    stage_hunk.py --list-hunks [--staged] <file>
    stage_hunk.py --list-lines [--staged] <file>

Indices are 1-based and match the order printed by the corresponding --list-*
mode, which uses `git diff -U0`. A hunk is a contiguous run of changed lines;
--lines addresses the individual lines inside one. Does not commit.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import NoReturn


def chdir_to_repo_for(file: str) -> str:
    """Resolve `file` to absolute, chdir to its directory, and return the absolute path.

    Lets the script work regardless of the caller's cwd: all subsequent `git`
    calls run inside the target file's repository.
    """
    abspath = os.path.abspath(file)
    parent = os.path.dirname(abspath) or "."
    if not os.path.isdir(parent):
        die(f"directory does not exist: {parent}")
    os.chdir(parent)
    return abspath

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def usage() -> NoReturn:
    prog = "stage_hunk.py"
    print(f"Usage: {prog} <file> <N|N-M> [...]", file=sys.stderr)
    print(f"       {prog} --lines <file> <N|N-M> [...]", file=sys.stderr)
    print(f"       {prog} --unstage [--lines] <file> <N|N-M> [...]", file=sys.stderr)
    print(f"       {prog} --list-hunks [--staged] <file>", file=sys.stderr)
    print(f"       {prog} --list-lines [--staged] <file>", file=sys.stderr)
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


@dataclass
class ChangedLine:
    hunk: int  # 1-based index of the U0 hunk this line sits in
    side: str  # "+" or "-"
    lineno: int  # new-side number for "+", old-side number for "-"
    text: str


def collect_changed_lines(diff_u0: str) -> list[ChangedLine]:
    """Every changed line in the file, numbered in diff order.

    A U0 diff has no context lines, so this is exactly the set of lines a
    caller can select. Each line is addressed on the side it exists: an
    addition by its new-side number, a deletion by its old-side number.
    """
    _, hunks = parse_diff(diff_u0)
    changed: list[ChangedLine] = []
    for hunk_idx, h in enumerate(hunks, start=1):
        new_line, old_line = h.new_start, h.old_start
        for raw in h.lines:
            tag = raw[:1]
            if tag == "+":
                changed.append(ChangedLine(hunk_idx, "+", new_line, raw[1:]))
                new_line += 1
            elif tag == "-":
                changed.append(ChangedLine(hunk_idx, "-", old_line, raw[1:]))
                old_line += 1
    return changed


def resolve_line_selection(
    diff_u0: str, wanted: set[int]
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], int]:
    """Map wanted 1-based line indices to single-line ranges on their own side.

    Unlike hunk selection, a deletion never reaches new_ranges — see the
    strict_sides note in build_patch.
    """
    changed = collect_changed_lines(diff_u0)
    new_ranges: list[tuple[int, int]] = []
    old_ranges: list[tuple[int, int]] = []
    for idx, cl in enumerate(changed, start=1):
        if idx not in wanted:
            continue
        if cl.side == "+":
            new_ranges.append((cl.lineno, cl.lineno))
        else:
            old_ranges.append((cl.lineno, cl.lineno))
    return new_ranges, old_ranges, len(changed)


def warn_split_modifications(diff_u0: str, wanted: set[int]) -> None:
    """Flag a selection that takes part of a modification.

    A changed line is a "-"/"+" pair. Staging one side alone is legal and
    occasionally wanted, but it leaves both the old and the new line in the
    index, so say so rather than let it pass silently.
    """
    changed = collect_changed_lines(diff_u0)
    by_hunk: dict[int, list[int]] = {}
    for idx, cl in enumerate(changed, start=1):
        by_hunk.setdefault(cl.hunk, []).append(idx)
    for hunk_idx, indices in by_hunk.items():
        sides = {changed[i - 1].side for i in indices}
        selected = [i for i in indices if i in wanted]
        if len(sides) == 2 and selected and len(selected) != len(indices):
            picked = " ".join(str(i) for i in selected)
            print(
                f"note: hunk {hunk_idx} rewrites lines (both - and +) and you selected"
                f" only {picked} of it — the index will hold both the old and the new line",
                file=sys.stderr,
            )


def parse_index_args(args: list[str], *, unit: str) -> set[int]:
    """Expand "3" and "3-5" arguments into a set of 1-based indices."""
    wanted: set[int] = set()
    for arg in args:
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", arg)
        if not m:
            print(
                f"error: expected {unit} index or range (e.g. 3 or 3-5), got: {arg}",
                file=sys.stderr,
            )
            usage()
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) is not None else lo
        if lo < 1:
            print(f"error: {unit} indices start at 1, got: {arg}", file=sys.stderr)
            usage()
        if hi < lo:
            print(f"error: reversed range: {arg}", file=sys.stderr)
            usage()
        wanted.update(range(lo, hi + 1))
    return wanted


def build_patch(
    diff: str,
    new_ranges: list[tuple[int, int]],
    old_ranges: list[tuple[int, int]],
    *,
    unstage: bool,
    strict_sides: bool = False,
) -> str | None:
    """Rebuild a patch containing only the selected changes.

    Each emitted hunk derives its @@ header from its own coordinates — no cross-
    hunk state leaks. new_start differs by mode: when staging we apply selected
    hunks onto the index, so positions accumulate only emitted deltas; when
    unstaging the index frame is fixed, so each hunk keeps its original new_start.

    strict_sides governs how a deletion is matched. Hunk selection puts a whole
    rewrite hunk in new_ranges, so a deletion has to be reachable by the new-side
    position it would have occupied. Line selection addresses each side
    separately, and that same fallback would drag in the deletion paired with a
    selected addition — so under strict_sides a deletion matches old_ranges only.
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
                matched = in_ranges(old_line, old_ranges) or (
                    not strict_sides and in_ranges(new_line, new_ranges)
                )
                if matched:
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


def list_lines(file: str, *, staged: bool) -> None:
    diff = read_diff(file, staged=staged, context=0)
    if not diff:
        die(f"no {'staged' if staged else 'unstaged'} changes in {file}")
    changed = collect_changed_lines(diff)
    for idx, cl in enumerate(changed, start=1):
        text = cl.text if len(cl.text) <= 80 else cl.text[:77] + "..."
        verb = "add" if cl.side == "+" else "del"
        addr = f"{cl.side}{cl.lineno}"
        print(f'line {idx}: {addr:<8} {verb}  hunk {cl.hunk}  "{text}"')


def stage(file: str, indices: list[str], *, unstage: bool, by_line: bool) -> None:
    diff = read_diff(file, staged=unstage, context=None)
    if not diff:
        die(f"no {'staged' if unstage else 'unstaged'} changes in {file}")

    unit = "line" if by_line else "hunk"
    wanted = parse_index_args(indices, unit=unit)

    diff_u0 = read_diff(file, staged=unstage, context=0)
    if by_line:
        new_ranges, old_ranges, total = resolve_line_selection(diff_u0, wanted)
    else:
        new_ranges, old_ranges, total = resolve_selection(diff_u0, wanted)
    if not new_ranges and not old_ranges:
        die(f"no {unit}s matched {' '.join(indices)} (file has {total} {unit}s)")
    if max(wanted) > total:
        beyond = " ".join(str(i) for i in sorted(wanted) if i > total)
        print(f"note: ignoring {unit}s past the end of the file: {beyond}", file=sys.stderr)
    if by_line:
        warn_split_modifications(diff_u0, wanted)

    patch = build_patch(diff, new_ranges, old_ranges, unstage=unstage, strict_sides=by_line)
    if patch is None:
        die(f"no {unit}s matched {' '.join(indices)} in {file}")

    if not apply_patch(patch, unstage=unstage):
        print("error: generated patch failed to apply", file=sys.stderr)
        print("patch content:", file=sys.stderr)
        print(patch, file=sys.stderr)
        sys.exit(1)

    verb = "unstaged" if unstage else "staged"
    print(f"{verb} {unit}s {' '.join(indices)} from {file}")
    print(git("diff", "--cached", "--stat", "--", file).stdout, end="")


def main(argv: list[str]) -> None:
    if argv and argv[0] in ("--list-hunks", "--list-lines"):
        mode = argv[0]
        rest = argv[1:]
        staged = False
        if rest and rest[0] == "--staged":
            staged = True
            rest = rest[1:]
        if len(rest) != 1:
            usage()
        lister = list_hunks if mode == "--list-hunks" else list_lines
        lister(chdir_to_repo_for(rest[0]), staged=staged)
        return

    unstage = by_line = False
    while argv and argv[0] in ("--unstage", "--lines"):
        if argv[0] == "--unstage":
            unstage = True
        else:
            by_line = True
        argv = argv[1:]
    if len(argv) < 2:
        usage()
    stage(chdir_to_repo_for(argv[0]), argv[1:], unstage=unstage, by_line=by_line)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"bug: stage-hunk crashed unexpectedly ({exc}) — please report this", file=sys.stderr)
        sys.exit(1)
