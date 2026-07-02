# Code Comment Standards

A comment earns its place only by carrying information the code cannot. Flag the non-obvious — what the next reader must know before changing the code — never restate what the code already says.

## Rules

- **Comment the non-obvious, never the obvious.** Keep comments short and packed with value. Do not narrate what the code does or write help text above it. Reserve comments for the surprising: "this looks wrong but…", a constraint that isn't visible locally, an ordering that matters.
- **Never narrate past state in prose.** Do not describe what the code used to do unless it is crucial to understanding the present. When it is, comment out the original code instead of paraphrasing: real code carries more than a paragraph, and sits where the reader is rather than lost in version control. Same bar as any comment — if the old code adds nothing, delete it rather than comment it.
- **No stale-prone references.** Do not name filenames, symbols, or anything else that drifts, unless the reference clearly earns its maintenance.
- **Never restate a constant's value.** A comment that quotes a value defined in the code below will go stale and end up asserting the opposite of the truth.
