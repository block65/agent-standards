# Pull Request Authoring

The [Git](git.md) rules bind a pull request too: the title follows the
conventional-commit subject rules, and the body states why, not what. A body
writable from `git diff` alone gets rewritten as why.

Write at most two paragraphs of prose, in the present tense, describing the tree
after the merge. State what the change enables, who gains from it, and by how
much where that is measurable. Add a line where one of these applies:

- a rejected alternative a reviewer would otherwise propose, with the reason
- an order the merge depends on: a migration, a dependent release, a flag to
  flip first
- verification performed by hand

Keep it forward-looking. A `fix:` states the failure it removes in one line, and
a migration names what a consumer changes; leave out the prior behaviour and
denials of worries nobody raised.

Outside a release pull request, name no version: the number depends on what
merges first, so the release notes carry it.

Leave the diff and the mechanism to the files; a paraphrase goes stale on the
next push and, under a squash merge, becomes the commit message. A pull request
that fully resolves an issue carries `Closes #N` so a squash keeps the
auto-close.

Where the project checks in a pull request template, fill its fields and add no
others. With no template, write the body without headings (no `## Summary`,
`## Changes`, `## Test plan`), per-file or per-commit walkthroughs, a repeat of
the title, or the branch's own history.

Add a task list (`- [ ]`) only when the author will tick it before merge.

BAD: narrates the mechanism, states no gain, denies an unraised worry

```text
[Component] includes only the [Item]s its [Caller]s use, because each names
them at build time and the bundler drops the rest. [Property] is unchanged.
```

GOOD: states the gain, its size, and the work left for consumers

```text
[Consumer] ships [Measure] less [Resource]. A [Caller] on the default [Setting]
needs no change; one that set [Option] names its [Item]s through [Api].
```
