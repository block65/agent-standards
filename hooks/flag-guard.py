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

Only `flag` findings are used. A `judge` finding needs a reading of the code and
has no business stopping a turn.
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

ADVICE = (
    "Fix these before continuing. Each is decidable from the text alone: delete a "
    "comment that explains deleted code, convert a misplaced /** */ block to //, and "
    "write a state predicate as the states accepted. If a finding is wrong, say so in "
    "your reply and end the turn; this will not block you twice."
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
        return [f for f in json.loads(proc.stdout or "[]") if f["disposition"] == "flag"]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def describe(items: list[dict]) -> str:
    shown = items[:MAX_REPORTED]
    lines = [f"diff-check: {len(items)} flagged in files you edited this session."]
    for item in shown:
        head = item["snippet"].splitlines()[0]
        lines.append(f"  {item['path']}:{item['line']} [{item['kind']}] {head}")
        lines.append(f"    {item['rule']}")
    if len(items) > len(shown):
        lines.append(f"  ... and {len(items) - len(shown)} more.")
    lines.append(ADVICE)
    return "\n".join(lines)


def emit_context(event: str, items: list[dict]) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": describe(items),
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
        if mine:
            emit_context(event, mine)
        return 0

    # The runtime sets this once it has seen a hook refuse the same turn. Standing
    # down here is what stops the loop that ended a session dead.
    if payload.get("stop_hook_active"):
        return 0

    touched = edited_files(session)
    if not touched:
        return 0

    items = [f for f in findings(cwd) if f["path"] in touched]
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
