# Code Comment Standards

A comment earns its place only by carrying information the code cannot. Flag the non-obvious: what the next reader must know before changing the code. Never restate what the code already says.

## Rules

- **Comment the non-obvious, never the obvious.** Keep comments short and packed with value. Do not narrate what the code does or write help text above it. Reserve comments for the surprising: "this looks wrong but…", a constraint that isn't visible locally, an ordering that matters.
- **Never narrate past state in prose.** Do not describe what the code used to do unless it is crucial to understanding the present. When it is, quote the crucial original expression in the comment instead of paraphrasing: real code carries more than a paragraph. One line, not a resurrected block; commented-out code rots like any dead code, and the same bar applies: if the old expression adds nothing, delete it.
- **Never explain a line by pointing somewhere else.** Naming another file, module, package, caller, or a concept that lives outside this file makes the comment wrong as soon as the other side moves, and nothing in review connects the two. Explain the code in front of you or delete the comment. A symbol or filename appears only where the reference clearly earns its maintenance.
- **Never restate a constant's value.** A comment that quotes a value defined in the code below will go stale and end up asserting the opposite of the truth.
- **No snapshot facts.** Never record measurements from a particular run: failure counts, timings, which tasks passed. They hold for one commit and are silently wrong after the next. Restating a constant's value (above) is one case of this.
- **A known fix is a task, not a comment.** If a comment can state the fix, apply it or file an issue and reference it. A comment version is a task with no owner and no close.
- **Shortening a comment must not change its claim.** Delete words or delete the comment; never swap the true reason for a plausible generic one.
- **Write it as prose.** One or two complete sentences, sentence case, full stop, following [Writing (Base)](../writing/base.md). Not a label (`// get user`), not a fragment, not a heading.

## Form in JavaScript & TypeScript

Which syntax to use is not a style preference: the two forms are read by different tools. (Rust documents public items with `///`; see [Rust Core](../lang/rust/core.md).)

- **JSDoc documents a declaration for its callers; `//` explains code for whoever changes it.** JSDoc is the editor's hover text, so it carries what the thing is for and nothing a caller wouldn't need. A warning, a constraint, the reason the code is written the way it is: that reader is inside the body, so it is `//` beside the line it binds, even when the declaration is exported. A JSDoc block floating in a body or sitting above a local `const` is a line comment written wrong.
- **Never a bare `/* */` block.** It is neither of the above. This includes commented-out code, which is deleted, not parked.
- **No tags that restate the types.** `@param`, `@returns`, `@type`, and `@typedef` duplicate the signature and go stale independently of it. The types are the documentation. `@deprecated` earns its place: the editor and the linter act on it.
- **One sentence stays on one line:** `/** Text. */`.

```ts
// BAD: narrates the code
// Map the users to their ids
// BAD: depends on something outside this file
// The ingest worker expects this sorted
// BAD: restates the signature
/** @param id - the id @returns the record */
// BAD: a reason for whoever edits the body, written as hover text
/** [Reason the code is written this way]. */

// GOOD: carries what the code cannot
// [Constraint or surprise the code cannot express].
```
