# Agent Instructions

Read `index.md` and follow its "Always load" standards. Before editing any
document here, read `writing/base.md` and `writing/technical.md`: this repo
dogfoods its own standards.

Paths here are root-relative. Consumers mount this repo as a submodule at
`agent-standards/`, so an instruction written for consumers uses that prefix.

## Commands

```sh
just                                  # typecheck, lint, fmt-check, plugin test, dead-code
just fmt                              # oxfmt, markdown included
skills/stage-hunk/tests/run-tests.sh  # stage-hunk script evals
skills/diff-check/tests/run-tests.sh  # diff-check script evals
just eval                             # agents with vs without the standards; costs usage
```

`just eval` runs each task in `evals/tasks/` headless, once bare and once with
the standards mounted, and scores the code with lint, tsc and a model judge.
Add a task when a review keeps catching the same mistake. Its prompt must not
name the rule it tests.

## What ships

1. **The standards**, consumed at `main` with no pinned SHA, so every commit
   reaches consumers on their next sync. Keep `main` releasable.
2. **The `block65-tools` plugin**: `.claude-plugin/plugin.json`,
   `skills/*/SKILL.md` and `hooks/`, listed in
   `.claude-plugin/marketplace.json`. Bump the plugin version when skills or
   hooks change.

Hooks bind where a standard only advises. Ship a hook check only for a rule
decidable from the text alone, and let it block once, so a disputed finding
cannot trap a turn.

## Writing a standard

- List it in `index.md`, or it never loads. "Always load" costs every agent
  context on every task; reserve it for rules that apply to all work, and give
  every other entry a description of when to load it.
- Keep a line only if removing it would cause a mistake. Cut what a current
  model does unaided, what the linter enforces, and repeats of other standards.
- Rules go here, facts go in compend: where a doc overlaps library or language
  documentation, give a one-line `compend get <collection> <topic>` pointer
  (see `lang/rust.md`).
- Give one example, with generic identifiers, and a one-clause reason where the
  rule is not obvious.
- State the rule as what to do, without capitals for emphasis, and scope an
  absolute rule to the frame it binds.
- Link between docs relative to the linking file, so links survive any
  submodule path.
- Commit scope is the area: `docs(lang): …`, `chore(plugin): …`.

## Skills

Each skill is `skills/<name>/SKILL.md`, with optional `scripts/` and `tests/`.
The `description` is the only trigger: list the phrasings a user would say,
key use case first, within 1,024 characters. Grant no tool the instructions do
not use.
