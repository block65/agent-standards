#!/usr/bin/env python3
"""Refuse the first write to a settings file, so a permission grant is never silent.

The failure this exists for: an agent hits one tool refusal, reports it as a
standing blocker, and proposes a permanent entry in `permissions.allow` as the
remedy. The refusal was transient and the grant outlives it. Recorded as the
addendum in `agent-coding-failure-modes.md`.

An edit made because the user asked and an edit made on a bad premise produce the
same diff, so nothing in the text separates them. What does separate them is
whether anyone repeats the request: the `update-config` skill runs on an explicit
instruction and simply tries again, while an agent improvising a fix has to say
out loud what it wanted and why. So this denies once per file per session and
then stands aside, the same shape `flag-guard.py` uses at `Stop`.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

SETTINGS_NAMES = {"settings.json", "settings.local.json"}
SETTINGS_DIR = ".claude"

REASON = (
    "Denied once: {path} carries the permission boundary, and this hook cannot tell "
    "a change the user asked for from one improvised to route around an error.\n"
    "If a tool call failed, retry it before treating it as blocked. A single refusal "
    "is a retry, not a finding, and widening permissions is not a fix for a failure "
    "that has not been reproduced.\n"
    "If the user asked for this change, or you have now told them what you are adding "
    "and why, make the same call again and it will go through."
)


def blocked_path(session: str) -> str:
    return os.path.join(
        tempfile.gettempdir(), f"settings-guard-{session or 'nosession'}.blocked"
    )


def already_denied(session: str, target: str) -> bool:
    try:
        with open(blocked_path(session), encoding="utf-8") as fh:
            return target in {line.strip() for line in fh}
    except OSError:
        return False


def record_denial(session: str, target: str) -> bool:
    try:
        with open(blocked_path(session), "a", encoding="utf-8") as fh:
            fh.write(target + "\n")
        return True
    except OSError:
        return False


def is_settings_file(path: str) -> bool:
    head, name = os.path.split(os.path.normpath(path))
    return name in SETTINGS_NAMES and os.path.basename(head) == SETTINGS_DIR


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    target = (payload.get("tool_input") or {}).get("file_path", "")
    if not target or not is_settings_file(target):
        return 0

    session = payload.get("session_id", "")
    target = os.path.join(payload.get("cwd") or os.getcwd(), target)
    if already_denied(session, target):
        return 0

    # A denial that cannot be recorded would repeat on every retry, which is the
    # loop this design exists to avoid. Failing open costs one ungated write.
    if not record_denial(session, target):
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": REASON.format(path=target),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
