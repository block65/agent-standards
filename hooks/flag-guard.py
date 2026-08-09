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

Only `flag` findings block. A `judge` finding needs a reading of the code and has
no business stopping a turn — but blocking and mentioning are different powers,
and the analysis is already computed. So `PostToolUse` also reports judgeable
findings on the file just written, where the agent still has the code in hand and
nothing is at stake if it disagrees.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

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
    "Fix these before continuing. Each is decidable from the text alone: delete a "
    "comment that explains deleted code, convert a misplaced /** */ block to //, and "
    "write a state predicate as the states accepted. If a finding is wrong, say so in "
    "your reply and end the turn; this will not block you twice."
)

JUDGE_ADVICE = (
    "Nothing here blocks you. Rate each against engineering/comments.md while you "
    "still have the code in hand: a comment earns its place only by carrying what the "
    "code cannot. Cut it to the sentence that does, or delete it."
)


def state_path(session: str, suffix: str) -> str:
    return os.path.join(
        tempfile.gettempdir(), f"diff-check-{session or 'nosession'}.{suffix}"
    )


def edited_files(session: str) -> set[str]:
    try:
        with open(state_path(session, "edited"), encoding="utf-8") as fh:
            return {line.strip() for line in fh if line.strip()}
    except OSError:
        return set()


def record_edit(session: str, path: str) -> None:
    try:
        with open(state_path(session, "edited"), "a", encoding="utf-8") as fh:
            fh.write(path + "\n")
    except OSError:
        pass


def findings(cwd: str) -> list[dict]:
    """Never let a check break the session: any failure here reports nothing."""
    try:
        proc = subprocess.run(
            [sys.executable, CHECK, "--json"],
            cwd=cwd,
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

    if not os.path.isdir(os.path.join(cwd, ".git")):
        return 0

    if event == "PostToolUse":
        edited = (payload.get("tool_input") or {}).get("file_path", "")
        if not edited:
            return 0
        target = os.path.relpath(edited, cwd)
        record_edit(session, target)
        mine = [f for f in findings(cwd) if f["path"] == target]
        if flags(mine) or judges(mine):
            emit_context(event, flags(mine), judges(mine))
        return 0

    # The runtime sets this once it has seen a hook refuse the same turn. Standing
    # down here is what stops the loop that ended a session dead.
    if payload.get("stop_hook_active"):
        return 0

    touched = edited_files(session)
    if not touched:
        return 0

    # Stop is the blocking event, so only what the text alone decides reaches it.
    items = flags([f for f in findings(cwd) if f["path"] in touched])
    if not items:
        return 0

    blocked = state_path(session, "blocked")
    if os.path.exists(blocked):
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
