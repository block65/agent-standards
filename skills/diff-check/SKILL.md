---
name: diff-check
description: "Rate the comments and check the changed lines in a diff against the recurring failure modes in agent-written code — narration comments, JSDoc used as an internal note, defensive defaults, sentinels, negated state predicates, magic numbers. Use this skill when the user says 'check my comments', 'rate these comments', 'are these comments any good', 'check the diff', 'diff check', 'did I narrate', 'review my changes before I commit', 'check what I just wrote', or asks whether a comment earns its place. Also use it before reporting a change complete, and when the user complains about comment spam, JSDoc blocks on internal code, or comments explaining code that is no longer there. Pass file paths as args to rate the comments already in those files instead of a diff."
allowed-tools: Bash(*/diff_check.py *), Read, Edit
---

Comment and change checks scoped to the lines a diff touched. Repo-wide the same
rules produce four figures of findings and get muted; on one change they produce a
handful.

## Run it

The script path is always `${CLAUDE_PLUGIN_ROOT}/skills/diff-check/scripts/diff_check.py`.
Use that exact form so the shell expands the variable. If `$CLAUDE_PLUGIN_ROOT` is
empty, stop and report back.

```
diff_check.py                    # working tree and staged, plus untracked files
diff_check.py --staged           # only what is about to be committed
diff_check.py --range main...    # a branch
diff_check.py --comments         # comments only
diff_check.py --lint             # add oxlint no-magic-numbers, changed lines only
diff_check.py src/a.ts src/b.ts  # rate the comments already in these files
diff_check.py --json             # machine-readable
```

One call. Do not run it per file.

## Act on the output

`FLAG` is decided — the pattern is the defect. Fix it without deliberating.

`JUDGE` is a candidate. Read the code around it and rule on it. A candidate that
survives is not a finding; say nothing about it.

| kind                  | what to do with a FLAG                                                                                                                                                                                               |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `comment-on-deletion` | Delete the comment. It narrates a removal in prose and sits beside the deletion. Keep it only if the removed behaviour is needed to understand the present code, and then quote the original expression in one line. |
| `jsdoc-misuse`        | Convert to `//`. A `/** */` block on a statement or an indented local documents nothing and shows up on hover as if it did. On a member of an interface, enum or class it is correct and is not reported.            |
| `bare-block`          | Convert to `//`, or delete if it is commented-out code.                                                                                                                                                              |
| `negated-state`       | Rewrite as the states accepted (`state = 'open'`), not the one excluded. A negation admits every state nobody has thought of yet.                                                                                    |

## Rate a comment

Each comment arrives with the code it sits above, on the `describes` line. Rate the
comment against that code and return one verdict per comment.

- **DELETE** — restates what the code says, labels it (`// get user`), describes the
  diff rather than the behaviour, records a measurement from one run, or states a
  reason nothing supports. Most comments an agent adds are this.
- **REWRITE** — the information is real but the form is wrong: it points at another
  file, quotes a value defined below it, states a fix that should be a task, or runs
  long enough to bury the code.
- **KEEP** — carries what the code cannot: a constraint invisible locally, an
  ordering that matters, a case that looks wrong and is not.

A rationale claim ("X wanted this", "this was needed for Y") is DELETE unless the
commit, ADR or issue that decided it can be named. Confidence is not evidence.

Report verdicts as a list of `path:line — VERDICT — reason in one clause`. No preamble.

## The judgement calls

- `comment-added` — apply the rating above.
- `sentinel` — `?? ""` and `?? []` are correct when the empty value is valid in the
  domain, and a defect when they make a missing required value indistinguishable
  from a supplied one. Decide which, from the consumer.
- `shell-default` — a default for a required value is a defect; `${TMPDIR:-/tmp}` is
  not. Ask whether the program can do the right thing when the value is absent.
- `magic-number` — a literal earns its place if the line already names it. Otherwise
  bind it to a named constant.

## Scope

The script reads. It does not stage, commit, or edit. Fix what it flags only when the
caller asked for fixes; otherwise report.
