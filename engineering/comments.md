# Code Comment Standards

A comment earns its place only by carrying information the code cannot.

## Rules

- **Comment the non-obvious, never the obvious.** Reserve comments for what the
  next reader must know before changing the code: "this looks wrong but…", a
  constraint not visible locally, an ordering that matters. Write one line
  trimmed to the constraint; a fragment is fine.
- **Never narrate past state in prose.** Describe the code as it is. Delete
  commented-out code.
- **Never explain a line by pointing somewhere else.** A comment naming another
  file, module, caller or outside concept goes wrong when that side moves, and
  review never connects the two. Explain the code in front of you or delete the
  comment; name a symbol only where the reference earns its maintenance.
- **No snapshot facts.** Omit a constant's value, run measurements, timings and
  pass counts: they are wrong after the next commit.
- **A known fix is a task, not a comment.** Apply it, or file an issue and
  reference it.
- **Delete a comment that carries nothing; tighten the why, never delete it.**
  Deletion is the default for a comment without value. One that carries a
  reason stays: shorten its words, never swap the true reason for a plausible
  generic one.

## Form in JavaScript & TypeScript

- **JSDoc documents a declaration for its callers; `//` explains code for
  whoever changes it.** JSDoc is hover text: what the thing is for, and only
  when the signature cannot say it. A warning, a constraint or the reason the
  code is written this way goes in a `//` beside the line it binds, even in an
  exported declaration.
- **No tags that restate the types.** Omit `@param`, `@returns`, `@type` and
  `@typedef`; the signature is the documentation. Keep `@deprecated`: the
  editor and linter act on it.
- **Exported function documentation uses multiline JSDoc,** never a one-line
  `/** Text */` or `//`. Delete a comment that repeats the name or types instead
  of expanding it to fit the format.
- **At most one line above a class member or nested function;** consecutive
  `//` lines count as multiline. Put anything longer inside the implementation.

BAD: depends on something outside this file.

```ts
// Ingest worker expects this sorted
const ordered = items.toSorted(compare);
await save(ordered);
```

BAD: the tags restate the signature.

```ts
/**
 * Loads a record
 * @param id - the id
 * @returns the record
 */
export async function load(id: Id) {
	return store.get(id);
}
```

GOOD: the JSDoc says what the function is for, and the reason sits beside the
line it binds.

```ts
/**
 * [What the function is for]
 */
export async function load(id: Id) {
	// [Reason the code is written this way]
	return store.get(id);
}
```
