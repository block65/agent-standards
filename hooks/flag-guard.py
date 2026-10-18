#!/usr/bin/env python3
"""Turn the diff-check flags into a control rather than advice.

Every rule these flags encode was already written down, cited by name in review,
and broken again afterwards. So this runs whether or not an agent chooses to run
it: `PostToolUse` reports a flag on the file just written, and `Stop` refuses the
turn once while a flag is outstanding.

Three limits keep it from becoming the thing it is meant to prevent. It attributes
only to files the agent edited in this session, so a working tree that was already
dirty is nobody's fault. It blocks once per session. And it stands down entirely
while `stop_hook_active` is set, which is the runtime's own signal that a hook is
looping.

It is also scoped to what it can decide. An edit outside the repo is never in the
repo's diff, so it is neither recorded nor scanned, and the diff it does run is
narrowed to the files this session edited. Before that, a session that only wrote
scratch files paid for a whole-tree diff on every turn.

Only `flag` findings block. A `judge` finding needs a reading of the code and has
no business stopping a turn — but blocking and mentioning are different powers,
and the analysis is already computed. So `PostToolUse` also reports judgeable
findings on the file just written, where the agent still has the code in hand and
nothing is at stake if it disagrees.
"""

from __future__ import annotations

import glob
import json
import os
import stat
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "skills", "diff-check", "scripts", "diff_check.py")

# A block that lists everything is the essay this repo also bans.
MAX_REPORTED = 12

# A one-line comment is cheap to read and the flag checks already decide the
# defects it can carry. Length is what makes "does this earn its place" a real
# question, so that is the floor for raising a comment nobody has to fix.
COMMENT_KINDS = {"comment-added", "comment-on-deletion"}
JUDGE_MIN_LINES = 3

ADVICE = (
    "Fix these before continuing: a comment added beside the code it says was "
    "removed. Delete it, or quote the original expression in one line where the "
    "present code cannot be understood without it. If a finding is wrong, say so in "
    "your reply and end the turn; this will not block you twice."
)

JUDGE_ADVICE = (
    "Nothing here blocks you. Rate each against engineering/comments.md while you "
    "still have the code in hand: a comment earns its place only by carrying what the "
    "code cannot. Cut it to the sentence that does, or delete it."
)


# A session's state outlives it, since nothing tells the hook a session ended.
# A week is past any session still worth attributing edits to.
STATE_MAX_AGE = 7 * 24 * 3600


def state_dir() -> str | None:
    """Per user and private: the edited list names files, and a shared temp dir
    lets anyone else plant the path first. None when that cannot be had."""
    path = os.path.join(tempfile.gettempdir(), f"diff-check-{os.getuid()}")
    try:
        os.makedirs(path, mode=0o700, exist_ok=True)
        info = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        return None
    if stat.S_IMODE(info.st_mode) & 0o077:
        return None
    return path


def state_path(session: str, suffix: str) -> str | None:
    base = state_dir()
    if base is None:
        return None
    return os.path.join(base, f"{session or 'nosession'}.{suffix}")


def prune_state() -> None:
    """Drop stale sessions' files, and the world-readable ones earlier versions
    left directly in the temp dir once those sessions are stale too."""
    cutoff = time.time() - STATE_MAX_AGE
    base = state_dir()
    stale = glob.glob(os.path.join(tempfile.gettempdir(), "diff-check-*.edited"))
    stale += glob.glob(os.path.join(tempfile.gettempdir(), "diff-check-*.blocked"))
    for path in stale:
        try:
            info = os.lstat(path)
            if info.st_uid == os.getuid() and info.st_mtime < cutoff:
                os.unlink(path)
        except OSError:
            pass
    if base is None:
        return
    for entry in os.scandir(base):
        try:
            if entry.stat(follow_symlinks=False).st_mtime < cutoff:
                os.unlink(entry.path)
        except OSError:
            pass


def edited_files(session: str) -> set[str]:
    path = state_path(session, "edited")
    if path is None:
        return set()
    try:
        with open(path, encoding="utf-8") as fh:
            return {line.strip() for line in fh if line.strip()}
    except OSError:
        return set()


def record_edit(session: str, path: str) -> None:
    state = state_path(session, "edited")
    if state is None:
        return
    try:
        with open(state, "a", encoding="utf-8") as fh:
            fh.write(path + "\n")
    except OSError:
        pass


def repo_root(cwd: str) -> str | None:
    """The top level of the repo holding cwd, or None outside one. A `.git`
    directory test misses worktrees and submodules, where `.git` is a file, and
    any session started below the top level."""
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return os.path.realpath(proc.stdout.strip())


def inside_repo(cwd: str, path: str) -> str | None:
    """The repo-relative path, or None when the file lives outside the repo."""
    try:
        rel = os.path.relpath(path, cwd)
    except ValueError:
        return None
    if rel.split(os.sep, 1)[0] == os.pardir:
        return None
    return rel


def findings(root: str, only: set[str]) -> list[dict]:
    """Never let a check break the session: any failure here reports nothing."""
    if not only:
        return []
    try:
        proc = subprocess.run(
            [
                sys.executable,
                CHECK,
                "--json",
                f"--repo={root}",
                *(f"--only={p}" for p in sorted(only)),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            return []
        return json.loads(proc.stdout or "[]")
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def flags(items: list[dict]) -> list[dict]:
    return [f for f in items if f["disposition"] == "flag"]


def judges(items: list[dict]) -> list[dict]:
    return [
        f
        for f in items
        if f["disposition"] == "judge"
        and (
            f["kind"] not in COMMENT_KINDS
            or len(f["snippet"].splitlines()) >= JUDGE_MIN_LINES
        )
    ]


def rows(items: list[dict]) -> list[str]:
    lines = []
    for item in items[:MAX_REPORTED]:
        head = item["snippet"].splitlines()[0]
        lines.append(f"  {item['path']}:{item['line']} [{item['kind']}] {head}")
        lines.append(f"    {item['rule']}")
    if len(items) > MAX_REPORTED:
        lines.append(f"  ... and {len(items) - MAX_REPORTED} more.")
    return lines


def describe(flagged: list[dict], judgeable: list[dict] = ()) -> str:
    lines: list[str] = []
    if flagged:
        lines.append(f"diff-check: {len(flagged)} flagged in files you edited this session.")
        lines.extend(rows(flagged))
        lines.append(ADVICE)
    if judgeable:
        lines.append(f"diff-check: {len(judgeable)} to rate, not blocking.")
        lines.extend(rows(judgeable))
        lines.append(JUDGE_ADVICE)
    return "\n".join(lines)


def emit_context(event: str, flagged: list[dict], judgeable: list[dict] = ()) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": describe(flagged, judgeable),
                }
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    session = payload.get("session_id", "")
    event = payload.get("hook_event_name", "")

    root = repo_root(cwd)
    if root is None:
        return 0

    if event == "PostToolUse":
        edited = (payload.get("tool_input") or {}).get("file_path", "")
        if not edited:
            return 0
        # Absolute, so an edit still attributes if the session's cwd moves.
        edited = os.path.realpath(os.path.join(cwd, edited))
        target = inside_repo(root, edited)
        if target is None:
            return 0
        record_edit(session, edited)
        mine = [f for f in findings(root, {target}) if f["path"] == target]
        if flags(mine) or judges(mine):
            emit_context(event, flags(mine), judges(mine))
        return 0

    # The runtime sets this once it has seen a hook refuse the same turn. Standing
    # down here is what stops the loop that ended a session dead.
    if payload.get("stop_hook_active"):
        return 0

    prune_state()
    touched = {
        rel
        for rel in (inside_repo(root, p) for p in edited_files(session))
        if rel is not None
    }
    if not touched:
        return 0

    # Stop is the blocking event, so only what the text alone decides reaches it.
    items = flags([f for f in findings(root, touched) if f["path"] in touched])
    if not items:
        return 0

    blocked = state_path(session, "blocked")
    if blocked is None or os.path.exists(blocked):
        emit_context(event, items)
        return 0

    try:
        with open(blocked, "w", encoding="utf-8") as fh:
            fh.write("1")
    except OSError:
        emit_context(event, items)
        return 0

    print(json.dumps({"decision": "block", "reason": describe(items)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
