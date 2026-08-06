# Code Comment Standards

A comment earns its place only by carrying information the code cannot. Flag the non-obvious — what the next reader must know before changing the code — never restate what the code already says.

## Rules

- **Comment the non-obvious, never the obvious.** Keep comments short and packed with value. Do not narrate what the code does or write help text above it. Reserve comments for the surprising: "this looks wrong but…", a constraint that isn't visible locally, an ordering that matters.
- **Never narrate past state in prose.** Do not describe what the code used to do unless it is crucial to understanding the present. When it is, quote the crucial original expression in the comment instead of paraphrasing: real code carries more than a paragraph. One line, not a resurrected block — commented-out code rots like any dead code, and the same bar applies: if the old expression adds nothing, delete it.
- **No stale-prone references.** Do not name filenames, symbols, or anything else that drifts, unless the reference clearly earns its maintenance.
- **Never restate a constant's value.** A comment that quotes a value defined in the code below will go stale and end up asserting the opposite of the truth.
- **No snapshot facts.** Never record measurements from a particular run: failure counts, timings, which tasks passed. They hold for one commit and are silently wrong after the next. Restating a constant's value (above) is one case of this.
- **A known fix is a task, not a comment.** If a comment can state the fix, apply it or file an issue and reference it. A comment version is a task with no owner and no close.
- **Shortening a comment must not change its claim.** Delete words or delete the comment; never swap the true reason for a plausible generic one.
