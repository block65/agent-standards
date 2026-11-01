# Code Comment Standards

A comment exists only where the code cannot tell the whole story: a constraint
not visible locally, an ordering that matters, the reason code that looks wrong
is right. A bad comment is worse than none, because the reader trusts it over
the code.

## A comment proves its worth; passing lint does not

Lint catches bad wording, not a comment with nothing to say. Each comment shows
what it carries that the code cannot. Delete it if the next reader, with only
the code, would make the same change correctly, whether or not lint flagged it.

A lint finding on a comment that carries a reason means the wording is wrong,
not the reason: rewrite it, never delete it to clear the warning. Deleting it
loses the reason, and the next reader changes the code without it. Clean lint
is a side effect of good comments, not the goal, as a passing suite is in
[Testing Philosophy](testing.md).

## Outside JavaScript and TypeScript

The comment lint runs only on JS and TS. Elsewhere, hold these by hand:

- Describe the code as it is: no past state, no commented-out code.
- Explain the code in front of you, not another file, caller or module.
- Leave out values that go stale: a constant's value, timings, pass counts.
- A known fix is a task: apply it, or file an issue and reference it.
