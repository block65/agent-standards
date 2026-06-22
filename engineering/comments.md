# Code Comment Standards

A comment earns its place only by carrying information the code cannot. Its job is to flag the non-obvious — warn the next reader of what they must know before changing the code — not to restate what the code already says.

## Rules

- **Comment the non-obvious, never the obvious.** Keep comments short and packed with value. Do not narrate what the code does or write help text above it. Reserve comments for the surprising: "this looks wrong but…", a constraint that isn't visible locally, an ordering that matters.
- **Never narrate past state in prose.** Do not describe what the code used to do unless it is crucial to understanding the present. When it is, comment out the original code instead of paraphrasing it: a few lines of real code carry what a paragraph would, surfaced where the reader is instead of left in version control for nobody to find. Same bar as any comment — if the old code adds nothing, delete it rather than comment it.
- **No stale-prone references.** Do not name-drop filenames, symbols, or anything else that drifts, unless the reference clearly adds value and is worth maintaining.
- **Never restate a constant's value.** A comment that quotes a value defined in the code below will go stale and end up asserting the opposite of the truth.
