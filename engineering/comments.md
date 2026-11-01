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
