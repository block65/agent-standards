---
name: stage-hunk
description: "Stages or unstages specific hunks, or individual lines within a hunk, from a changed file in a git repo without interactive prompts. Use whenever changes need partial staging or unstaging: committing only the bug fix hunk but not the refactor, taking one line out of a block of added lines, or unstaging something that was staged by mistake. Common phrases: 'commit only the X changes', 'stage that hunk', 'stage just that line', 'only the second of those lines', 'don't include the Y part', 'unstage the refactor'. Pass args as: first line = file path, remaining lines = plain-language description of which changes to (un)stage. Example args: \"src/foo.ts\\nstage only the import changes, leave the function rename\"."
model: haiku
context: fork
allowed-tools: Bash(git diff -U10 -- *), Bash(*/skills/stage-hunk/scripts/stage_hunk.py *)
---

Stage or unstage specific hunks from one file, then stop; committing is the
caller's job.

`$ARGUMENTS` is one string: everything before the first newline is the file
(absolute or relative; caller cwd does not matter), everything after is the
description of what to (un)stage. Words like "stage", "unstage" or "only" are
part of the description, not field labels. Read it verbatim, without asking the
caller to reformat. If there is no description, report back asking for one.

## Run the script

Always run it as
`${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py`, in exactly that
form, so the shell expands the variable. Use no relative path, no `cd` into a
development copy, and no glob under `~/.claude/plugins/cache/`. If the variable
expands empty, stop and report back.

The whole flow is two Bash calls, list then stage. Substitute the file path
inline: no shell variables, no echo, no probing, no per-hunk calls.

1. List the hunks (add `--staged` when unstaging):
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --list-hunks <file>
   ```
2. Convert the description into the listed indices; the script accepts only
   indices and ranges (`3`, `3-5`). Pass every index in one call:
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py <file> 1 3-5
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --unstage <file> 2
   ```
3. Report what was staged or unstaged.

When the description names part of a hunk, use the line-addressed pair instead,
with the same two-call budget; `--staged` and `--unstage` work the same:

```
${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --list-lines <file>
${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --lines <file> 2 5-7
```

A rewritten line is a `-`/`+` pair: select both to rewrite it; selecting one
leaves the old and new lines both in the index, and the script warns.

If the listing cannot be matched to the description, one
`git diff -U10 -- <file>` call is allowed, in exactly that form. If it still
cannot be matched, report back with a summary so the caller can clarify,
instead of guessing indices.

A mode change, an untracked file and a binary file have no hunks; pass the
script's message for them back to the caller unchanged.
