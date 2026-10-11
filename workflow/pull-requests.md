# Pull Request Authoring

The rule in [Git](git.md) binds a pull request body too: why, not what. The
title follows the conventional-commit subject rules in that document.

Write at most two paragraphs of prose, in the present tense, describing the tree
after the merge. State what the change enables, who gains from it, and by how
much where that is measurable. Add a line where one of these applies:

- a rejected alternative a reviewer would otherwise propose, with the reason
- an order the merge depends on: a migration, a dependent release, a flag to
  flip first
- verification performed by hand

Keep it forward-looking. A `fix:` states the failure it removes in one line;
beyond that, the prior behaviour and a denial of a worry nobody raised describe
a state the reader is about to stop caring about. Migration is the exception:
name what a consumer changes, since that is work still ahead of them.

Outside a release pull request, name no version. The commit type decides whether
a release happens at all, and the number falls out of whatever else merges
first, so a body promising one is wrong as soon as another branch lands ahead of
it. A consumer who needs the number reads the release notes, written once it
exists.

Leave the diff out. It is on the pull request, and the reviewer reads it. A body
paraphrasing it goes stale on the next push, and where the merge squashes, that
paraphrase becomes the commit message and stays in history. Describing the
mechanism is the same defect in longer form: state the benefit, and leave the
implementation to the files. For the same reason, a pull request that fully
resolves an issue carries `Closes #N`, per [Git](git.md), so a squash keeps the
auto-close.

Where the project checks in a pull request template, fill its fields and add no
others. With no template, the body carries no headings: no `## Summary`,
`## Changes`, `## Test plan` or similar. Also out: per-file and per-commit
walkthroughs, a repeat of the title, and the branch's own history ("started
with [Approach], switched to [Other]").

Add a task list (`- [ ]`) only when the author will tick it before merge; an
unticked box at merge reads as outstanding work.

One check before opening: a body writable from `git diff` alone gets rewritten
as why. [Git](git.md) applies the same test to the commit subject.

```
BAD: restates the diff
Adds [Function] to [Component] and updates [Caller] to pass [Argument].

BAD: narrates the mechanism, states no gain, denies an unraised worry
[Component] includes only the [Item]s its [Caller]s use, because each names
them at build time and the bundler drops the rest. [Property] is unchanged.

GOOD: states the gain, its size, and the work left for consumers
[Consumer] ships [Measure] less [Resource]. A [Caller] on the default [Setting]
needs no change; one that set [Option] names its [Item]s through [Api].
```
