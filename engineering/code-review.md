# Code Review Standards

Report every defect found, including the uncertain and low-severity ones, each
with its confidence and severity. Rank and drop them after the pass: a severity
bar applied while reading silently costs real defects.

Defects recur in these places; the list is not the limit of the search.

- Copy-pasted code, and a change to one function in a set that misses its
  counterparts.
- Data split or reshaped only to be reassembled later in the same path.
- A frame that narrows a value only to pass it on; see
  [Narrowing](narrowing.md).
- A `??` default that is not the absent case's defined behaviour: a sentinel,
  an arbitrary value, or a workaround for a parameter typed looser than its use.
- Log levels and log messages that do not match what happened.
- Inconsistent terminology.
- A renamed type whose old name survives in nearby comments and variables.
- A comment the change left behind; see [Comments](comments.md).
- Surrounding code left broken because it was "not part of the change".

Write a tool for a check that will recur, instead of a one-off script.
