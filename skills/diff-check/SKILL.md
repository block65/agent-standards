---
name: diff-check
description: "Rates the comments a diff adds against the code they claim to explain, flags prose that narrates code the same change deleted, and catches a deleted comment that carried a reason. Use when the user says 'check my comments', 'rate these comments', 'are these comments any good', 'check the diff', 'diff check', 'did I narrate', 'review my changes before I commit', 'check what I just wrote', or asks whether a comment earns its place. Also use before reporting a change complete, and when the user complains about comment spam, JSDoc blocks on internal code, or comments explaining code that is no longer there. Pass file paths as args to rate the comments already in those files instead of a diff."
allowed-tools: Bash(*/diff_check.py *), Read, Edit
---

Run the bundled script once (not per file), always by the path
`${CLAUDE_PLUGIN_ROOT}/skills/diff-check/scripts/diff_check.py` so the shell
expands the variable. If `$CLAUDE_PLUGIN_ROOT` is empty, stop and report back.

```
diff_check.py                    # working tree and staged, plus untracked files
diff_check.py --staged           # only what is about to be committed
diff_check.py --range <base>...  # a branch
diff_check.py src/a.ts src/b.ts  # rate the comments already in these files
diff_check.py --json             # machine-readable
```

`<base>` is what `git symbolic-ref --short refs/remotes/origin/HEAD` prints;
resolve it, never assume it.

The script only reads. Fix what it reports only when the caller asked for
fixes; otherwise report.

## Act on the output

`FLAG` is decided: the pattern is the defect. Fix it without deliberating.

`JUDGE` is a candidate. Read the code around it and rule on it. A candidate that
survives is not a finding; leave it out of the report.

`comment-on-deletion`: delete the comment. Keep it only where the removed
behaviour is needed to understand the present code, and then quote the original
expression in one line.

`reason-deleted`: the change removed a comment that gave a reason and added
nothing that keeps it. Deleting is the one edit guaranteed to lower a warning
count, so the why goes first under a backlog. Put the reason back, tightened to
a clause, unless the code now states it (a named constant, an assertion, a
type). Its `kept` lines are the comments the hunk added, for comparison.

## Rate a comment

Rate each comment against the code on its `describes` line, one verdict each.

- **DELETE**: restates or labels the code (`// get user`), describes the diff
  rather than the behaviour, records a measurement from one run, or states a
  reason nothing supports. Most comments an agent adds are this.
- **REWRITE**: the information is real but the form is wrong: it points at
  another file, quotes a value defined below it, states a fix that should be a
  task, or runs long enough to bury the code.
- **KEEP**: carries what the code cannot: a constraint invisible locally, an
  ordering that matters, a case that looks wrong and is not.

A rationale claim ("X wanted this", "this was needed for Y") is DELETE unless
the commit, ADR or issue that decided it can be named. Confidence is not
evidence.

Report one line per comment, `path:line — VERDICT — reason in one clause`, and
nothing before the list.
