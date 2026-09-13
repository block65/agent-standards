# Code Review Standards

Report every defect found, including the uncertain and the low-severity ones, each with its confidence and severity; rank and drop them after the pass, never while reading. A severity bar applied during the read silently costs real defects. The list below is where defects recur, not the limit of what to look for.

## Common Bugs

- Duplicated code chunks (copy-paste without abstraction).
- Splitting or modifying data types only to reassemble them later in the code path.
- A frame that narrows a value only to pass it on (stringify-to-pass, slice-to-pass, derive-to-pass) instead of passing it at its richest. See [Narrowing](narrowing.md).
- Changing one function in a common set but not its counterparts.
- Inappropriate log levels for messages.
- Incomprehensible log messages.
- Inconsistent terminology.
- Ignoring surrounding code ("not my code" mindset).

## Behaviours

- Write tools instead of one-off scripts.
- When refactoring or renaming a type, check surrounding code for comments and variable names referencing the old name.
- A comment left behind by a change is a defect in the change; see [Comments](comments.md).
