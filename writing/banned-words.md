# Banned Words

Words we don't use, grouped by why.

## Word choice

Banned from all output: prose, comments, commits, chat.

### Permanent

- "load bearing": say what depends on it.
- "seam": name the boundary (the interface, parameter or module edge).
- "honest": cut it, or say "accurate" or "complete".
- "fair": cut it, or say "reasonable" or "correct".
- "seed": when it means an origin, trigger, or starting point; name the thing
  itself. Literal uses (a random seed, a seed number, seeding a database, seed
  data) are fine.
- "fork": when it means a decision or branch point; say "decision" or "branch".
  Developers read "fork" as a git fork, so the figurative sense misleads.
  Literal uses (a git fork, `fork()`, forking a process/subagent) are fine.
- "ladder": say "order" or "sequence", and list the steps in it. Literal uses (a
  physical ladder, a ladder diagram) are fine.
- costume framing: one thing "wearing the costume of", "dressed up as",
  "masquerading as", or "disguised as" another. Name what the thing is and what
  it does: "introspection, not testing", not "introspection masquerading as
  testing".

### Flavour of the month

Currently-watched words. The date is when an entry was added, not an expiry; a
flavour can outlast its month. When editing this file, re-test entries older
than six months: remove one, and re-add it if the behaviour recurs.

- "tautology" (since 2026-05): say "restates" or "always true".
- "tension" (since 2026-05): say "conflict" or "trade-off".
- "smoking gun" (since 2025-08): say "evidence" and cite it.
- "tractable" (since 2026-06): say "solvable" or "feasible".
- "belt-and-braces" (since 2026-08): name the second safeguard.

## Action signal

These are cues, not forbidden text. They surface right before a big or
irreversible action. On reaching for one, stop and confirm with the user before
continuing.

- "NUKE"
