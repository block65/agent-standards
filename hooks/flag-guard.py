#!/usr/bin/env python3
"""Turn the diff-check flags into a control rather than advice.

Every rule these flags encode was already written down, cited by name in review,
and broken again afterwards. So this runs whether or not an agent chooses to run
it: `PostToolUse` reports a flag on the file just written, and `Stop` refuses the
turn while any flag is outstanding.

Only `flag` findings are used. A `judge` finding needs a reading of the code and
has no business stopping a turn.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "skills", "diff-check", "scripts", "diff_check.py")

ADVICE = (
    "Fix these before continuing. Each is decidable from the text alone: delete a "
    "comment that explains deleted code, convert a misplaced /** */ block to //, and "
    "write a state predicate as the states accepted. If a finding is wrong, say why "
    "in your reply rather than leaving it."
)


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
    lines = [f"diff-check: {len(items)} flagged, and every one is already a written rule."]
    for item in items:
        head = item["snippet"].splitlines()[0]
        lines.append(f"  {item['path']}:{item['line']} [{item['kind']}] {head}")
        lines.append(f"    {item['rule']}")
    lines.append(ADVICE)
    return "\n".join(lines)


def already_blocked(session: str, items: list[dict]) -> bool:
    """Block a given set of flags once. An agent that cannot fix them, or disputes
    them, must still be able to end the turn."""
    digest = hashlib.sha256(
        "".join(f"{i['path']}:{i['line']}:{i['kind']}" for i in items).encode()
    ).hexdigest()[:16]
    marker = os.path.join(
        tempfile.gettempdir(), f"diff-check-{session or 'nosession'}-{digest}"
    )
    if os.path.exists(marker):
        return True
    try:
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(digest)
    except OSError:
        pass
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return 0

    event = payload.get("hook_event_name", "")
    items = findings(cwd)
    if not items:
        return 0

    if event == "PostToolUse":
        # Report only the file the agent just touched, so the feedback lands on
        # the edit that caused it.
        edited = (payload.get("tool_input") or {}).get("file_path", "")
        if edited:
            target = os.path.relpath(edited, cwd)
            items = [i for i in items if i["path"] == target]
        if not items:
            return 0
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": describe(items),
                    }
                }
            )
        )
        return 0

    if already_blocked(payload.get("session_id", ""), items):
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
        return 0

    print(json.dumps({"decision": "block", "reason": describe(items)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
