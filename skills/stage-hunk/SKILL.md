---
name: stage-hunk
description: "Stage or unstage specific hunks from a changed file in a git repo without interactive prompts. Use this skill whenever you need to partially stage or unstage hunks — for example, committing only the bug fix hunk but not the refactor, or unstaging something that was staged by mistake. Common phrases: 'commit only the X changes', 'stage that hunk', 'don't include the Y part', 'unstage the refactor'. Pass args as: first line = file path, remaining lines = plain-language description of which changes to (un)stage. Example args: \"src/foo.ts\\nstage only the import changes, leave the function rename\"."
model: haiku
context: fork
allowed-tools: Bash(git diff *), Bash(*/stage-hunk.sh *), Bash(*/stage-hunk.sh --unstage *), Bash(*/stage-hunk.sh --list-hunks *)
---

You stage or unstage specific hunks from a file. You do NOT commit.

## Arguments

`$ARGUMENTS` is a single string with this structure:

- **First line** — the file path with changes (unstaged or staged).
- **Remaining lines** — a plain-language description of which changes to stage/unstage, or line numbers if known. May contain the words "stage", "unstage", "only", etc. — these are part of the description, not field labels.

Treat the whole `$ARGUMENTS` string verbatim. Do not look for `key: value` fields, do not ask the caller to re-format. Split on the first newline: everything before it is the file path; everything after it is the description.

If `$ARGUMENTS` is empty or contains only the file path with no description, report back asking the caller for the description — do not guess.

## Steps

1. Split `$ARGUMENTS` into `FILE` (first line) and `DESCRIPTION` (the rest).
2. List the available hunks:
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage-hunk.sh --list-hunks "$FILE"
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage-hunk.sh --list-hunks --staged "$FILE"
   ```
   Use `--staged` when the description asks to unstage. Prints each hunk with index, line range, and preview.
3. Match the `DESCRIPTION` to the listed hunks. Note: the script accepts plain integer hunk indices only — convert the description into the indices shown by `--list-hunks`.
4. Call the script with the hunk numbers from the list (plain integers, space-separated):
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage-hunk.sh "$FILE" 2
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage-hunk.sh "$FILE" 1 3 5
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage-hunk.sh --unstage "$FILE" 1
   ```
5. Report what was staged/unstaged.

If `--list-hunks` output is insufficient to match the description,
try `git diff -U10 -- "$FILE"` for more context. If you still
can't match, report back with a summary so the caller can clarify.

