---
name: stage-hunk
description: "Stage or unstage specific hunks from a changed file in a git repo without interactive prompts. Use this skill whenever you need to partially stage or unstage hunks — for example, committing only the bug fix hunk but not the refactor, or unstaging something that was staged by mistake. Common phrases: 'commit only the X changes', 'stage that hunk', 'don't include the Y part', 'unstage the refactor'. Pass args as: first line = file path, remaining lines = plain-language description of which changes to (un)stage. Example args: \"src/foo.ts\\nstage only the import changes, leave the function rename\"."
model: haiku
context: fork
allowed-tools: Bash(git diff *), Bash(*/stage_hunk.py *), Bash(*/stage_hunk.py --unstage *), Bash(*/stage_hunk.py --list-hunks *)
---

You stage or unstage specific hunks from a file. You do NOT commit.

## Arguments

`$ARGUMENTS` is a single string with this structure:

- **First line** — the file path with changes (unstaged or staged). Call this the *file*.
- **Remaining lines** — a plain-language description of which changes to stage/unstage, or line numbers if known. Call this the *description*. May contain the words "stage", "unstage", "only", etc. — these are part of the description, not field labels.

Treat the whole `$ARGUMENTS` string verbatim. Do not look for `key: value` fields, do not ask the caller to re-format. Mentally split on the first newline: everything before it is the file; everything after it is the description.

If `$ARGUMENTS` is empty or contains only the file path with no description, report back asking the caller for the description — do not guess.

## Steps

**Path rule — read before running any command:**

The script path is **always** `${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py`. Use that exact form in every Bash call so the shell expands `$CLAUDE_PLUGIN_ROOT`. Never substitute a relative path (`./skills/...`), never `cd` into a development copy of the plugin, never glob for the script under `~/.claude/plugins/cache/...`. If `$CLAUDE_PLUGIN_ROOT` is empty when you `echo` it, stop and report back — do not improvise.

The file may be absolute or relative to your cwd; the script resolves it to absolute and changes to the file's directory internally, so caller cwd does not matter.

**Procedure — minimum number of Bash calls. Do not prepare variables, do not echo, do not probe lengths, do not stage in batches.**

1. Mentally split `$ARGUMENTS` into the file and the description. Do not export shell variables for these; substitute the actual file path inline in the commands below.
2. List the available hunks — exactly one Bash call:
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --list-hunks <file>
   ```
   For unstaging, add `--staged`. Prints each hunk with index, line range, and preview.
3. Match the description to the listed hunks. The script accepts plain integer hunk indices only — convert the description into the indices shown by `--list-hunks`.
4. Stage (or unstage) all matched hunks in **one** Bash call — pass every index in a single invocation:
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py <file> 1 3 5
   ${CLAUDE_PLUGIN_ROOT}/skills/stage-hunk/scripts/stage_hunk.py --unstage <file> 2
   ```
   Do not run one command per hunk.
5. Report what was staged/unstaged.

The whole flow should be 2 Bash calls: list, then stage. If `--list-hunks` output is insufficient to match the description, you may add one `git diff -U10 -- <file>` call for more context. If you still can't match, report back with a summary so the caller can clarify — do not guess indices.
