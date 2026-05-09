# Code Review Standards

## Common Bugs
- Duplicated code chunks (copy-paste without abstraction).
- Splitting or modifying data types only to reassemble them later in the code path.
- Changing one function in a common set but not its counterparts.
- Inappropriate log levels for messages.
- Incomprehensible log messages.
- Inconsistent terminology.
- Ignoring surrounding code ("not my code" mindset).

## Behaviours
- Write tools instead of one-off scripts.
- When refactoring or renaming a type, check surrounding code for comments and variable names referencing the old name.
- The only thing worse than no comments is incorrect comments.
