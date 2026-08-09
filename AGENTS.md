# Agent Instructions

Guidance for any agent working in this repository

## Load the standards

**Always:** Read `index.md`, then follow all "Always load" standards listed there.
**Before editing any document in this repo:** STOP. Read `writing/base.md` then `writing/technical.md` and follow both.

This repo is the source of the standards, so it dogfoods them: every doc here must obey `writing/base.md` and `writing/banned-words.md`. Paths above are root-relative because the standards live at the root here. Consuming repos add this repo as a submodule at `agent-standards/` and reference `agent-standards/index.md`, so any instruction written _for consumers_ uses that prefix.

## Commands

```sh
just fmt          # oxfmt across the repo (markdown included), version pinned in the justfile
just fmt-check    # verify formatting without writing
skills/stage-hunk/tests/run-tests.sh    # eval suite for the stage-hunk script
skills/diff-check/tests/run-tests.sh    # eval suite for the diff-check script
```

Those two scripts are the only tested code here. There is no build, no lint, and no test runner beyond them; the deliverable is markdown.

## What this repo is

Two artefacts ship from the same tree:

1. **The standards**: markdown consumed as a git submodule at `agent-standards/`. Consumers track `main` (not a pinned SHA), so every commit reaches them on their next sync. Keep `main` releasable.
2. **The `block65-tools` plugin**: `.claude-plugin/plugin.json`, `skills/*/SKILL.md` and `hooks/hooks.json`, listed in `.claude-plugin/marketplace.json` alongside the sibling `compend` and `playwright-harness` plugins. Bump the plugin version when skills or hooks change.

Hooks are the part that binds. A standard an agent can decline to read is advice; `hooks/hooks.json` runs whether or not the agent chooses to. Ship a check there only when the rule it enforces is decidable from the text alone, and let it block once rather than repeatedly, so a disputed finding cannot trap a turn.

## Structure that matters

`index.md` is the barrel. It sorts every standard into three tiers (**Always load**, **Load if applicable (workflow)**, **Load if applicable (content)**), and consuming repos only reference the barrel. A new standard is not shipped until it is listed there under the right tier; adding an "Always load" entry silently costs every agent context on every task, so put a doc there only when it applies to all work.

Several docs are hubs rather than content:

- `lang/rust.md` → the modules under `lang/rust/`
- `writing/base.md` → `technical.md`, `marketing.md`, `adr.md` (each names base as a prerequisite)
- `engineering/testing.md` → prerequisite of `vitest.md` and `playwright.md`

Links between docs are relative to the linking file, which keeps them valid under any submodule path.

## Writing a standard

- **Facts belong in compend, rules belong here.** Where a doc overlaps library or language documentation, defer with a one-line `compend get <collection> <topic>` pointer instead of copying a summary that will drift (see `lang/rust.md`). On conflict, these standards win; say so explicitly.
- **Every line costs context in every consuming repo.** Compress prose, give one example not three, and use generic identifiers.
- **Absolute rules need a scope.** "Never X" that is wrong in some frame will be followed anyway; state the frame it binds.
- Commits are conventional with the area as scope: `docs(comments): …`, `docs(lang): …`, `feat(handover): …`, `chore(plugin): …`.

## Skills

Each skill is `skills/<name>/SKILL.md` with `name` and `description` frontmatter, and optional `scripts/` and `tests/`. The description is the trigger: it must enumerate the phrasings a user would actually say, since nothing else decides whether the skill fires. Grant no tool that the skill's own instructions do not use.
