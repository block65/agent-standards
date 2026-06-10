---
name: moonrepo
description: >
  Author, refactor, and debug moonrepo (moon) configuration — tasks, projects,
  workspaces, toolchains, plugins, and extensions — grounded in a locally cached,
  updatable copy of the official moon docs and JSON config schemas. Use this skill
  whenever the user wants to add or change a moon task, set up or restructure a moon
  workspace/project, share tasks across projects, configure a toolchain, write or use
  a WASM plugin or extension, migrate from moon v1 to v2, or fix a broken/misbehaving
  task. Trigger on any mention of moon.yml, .moon/workspace, .moon/toolchains,
  .moon/tasks, moon run / moon ci / moon query, task inheritance, `extends`, or
  "moonrepo" in general — even when the user just says "add a clean task to this
  package" in a repo that uses moon. moon v2 ("Phobos") is the default; v1 syntax is
  a frequent and costly trap, so always confirm version-correct config from the cache
  rather than from memory.
---

# moonrepo (moon) — config authoring, grounded in the real docs & schemas

moon evolves fast and **v2 broke a lot of v1 config** (`type`→`layer`, `platform`→
`toolchains`, single `.moon/tasks.yml`→`.moon/tasks/all.yml`, piped commands must use
`script:` not `command:`, and more). Writing moon config from memory is how you ship
v1 syntax into a v2 repo. This skill exists to stop that: it keeps a **local, cached,
one-command-updatable knowledge base** built from the official `moonrepo/moon` repo —
the full docs library plus the JSON config schemas rendered into dense, lossless field
references — and you answer from *that*, not from recall.

## The two jobs

1. **Authoring & refactoring (the main event).** "Add an astro `clean` task", "make
   `vite-clean` a shared task every frontend project inherits", "run two tasks with one
   command". This needs real understanding of moon's task model — see the
   [Task-authoring playbook](#task-authoring-playbook).
2. **Debugging.** A task fails, is skipped, won't cache, or caches when it shouldn't.
   moon ships an excellent official `debug-task` skill, vendored into the cache — see
   [Debugging](#debugging).

---

## Step 0 — make sure the cache exists (cache-first, sync on miss)

The knowledge base lives in a shared home dir so it survives plugin reinstalls and is
reused across every repo: `~/.claude/skills/moonrepo/cache/<version>/` (default
`v2/`). Check it:

```bash
ls ~/.claude/skills/moonrepo/cache/v2/schemas/ 2>/dev/null && \
ls ~/.claude/skills/moonrepo/cache/v2/docs/_index.md 2>/dev/null
```

**On a miss** (empty/absent), build it — one command, downloads once, then caches:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py"
```

This fetches the whole `website/docs` library, the v2 JSON schemas (rendered to dense
field tables), and the official `debug-task` skill, recording each file's git SHA so
re-runs skip unchanged files. See [Updating](#updating-the-knowledge-base) for refs,
v1, and optional distillation. Don't WebFetch moon docs into context as a "fallback" —
that defeats the cache; sync once and read locally.

### Which version? (v2 is default — confirm, don't assume)

v2 is the modern default. Only treat a repo as **v1** if you see concrete v1 signals —
a `.moon/tasks.yml` (single file, not a `tasks/` dir), `.moon/toolchain.yml`
(singular), `type:`/`platform:` in `moon.yml`, or a pinned `moon` version `< 2.0.0`.
When unsure, check:

```bash
moon --version 2>/dev/null            # CLI version, if installed
cat .prototools 2>/dev/null | grep -i moon
```

If the repo is v1, build and read the v1 tree (`sync.py --version v1`,
`cache/v1/...`) and lean on `cache/v2/docs/migrate/` for the deltas. **Never mix v1
and v2 syntax.**

---

## The lookup protocol — answer from the cache, never from memory

| You need… | Read from the cache |
|-----------|---------------------|
| Exact config options/types/defaults (what's allowed, what's required) | `schemas/<file>.md` — lossless field reference |
| The raw JSON schema (for a `$schema` pointer or deep detail) | `schemas/raw/<file>.json` |
| Concepts & best practice (inheritance, targets, tokens, caching…) | `docs/_index.md` → open the page |
| A specific guide (sharing, plugins, extensions, docker, CI…) | `docs/guides/<name>.mdx` |
| v1→v2 migration deltas | `docs/migrate/*` |
| Dense pre-distilled rules (if `--distill` was run) | `digests/<page>.md` |

The schema files map to the config files:

| Config file | Schema reference | Covers |
|-------------|------------------|--------|
| `.moon/workspace.*` | `schemas/workspace.md` | projects, vcs, pipeline, constraints, hasher |
| `.moon/toolchains.*` | `schemas/toolchains.md` | toolchain (WASM plugin) config |
| `.moon/tasks/**/*` | `schemas/tasks.md` | global/shared tasks, `inheritedBy`, implicit deps/inputs |
| `moon.*` (project) | `schemas/project.md` | metadata, `dependsOn`, `tasks`, overrides |
| `.moon/extensions.*` | `schemas/extensions.md` | extension registrations |
| template `*.yml` | `schemas/template.md` | codegen templates |

**Ground every config field you emit in `schemas/<file>.md`.** If a field isn't there,
it isn't real — don't invent it.

### Config format is the user's choice

moon v2 accepts **`.yml`/`.yaml`, `.json`/`.jsonc`, `.pkl`, `.hcl`, `.toml`**. Match
the format already used in the repo; if starting fresh, YAML is the documented default.
Pkl unlocks loops/variables (e.g. generating per-OS tasks) but needs the `pkl` binary
present at runtime. Whatever the format, add the `$schema` pointer when the repo does —
in v2 it points at the local `.moon/cache/schemas/<file>.json` (the hosted
`moonrepo.dev/schemas/*` URLs are deprecated in v2).

---

## Task-authoring playbook

This is where "be smart about creation" lives. A good moon task author reasons in this
order. Worked example throughout: **"add a `clean` task to our Astro app."**

### 1. Survey the existing moon setup FIRST — this is non-negotiable
The single biggest real-world failure is authoring in a vacuum: the agent takes the
instruction literally, wedges a brand-new self-contained task into one project, and
**ignores the structure the repo already has** — duplicating a concern that's already
modelled elsewhere. Don't be that agent. Before you write a single line, find out what
already exists.

**Ask moon what's really there (it resolves inheritance for you):**
```bash
moon project <id> --json     # every task this project ALREADY has, incl. inherited ones
moon task <id>:<name> --json # one resolved task: its command, inputs, deps, source file
```
If the CLI isn't available, read the config surface by hand — **all of it**:
- Root `.moon/` — `workspace.*`, `toolchains.*`, **`tasks/**`** (global/shared tasks),
  and any **`modules/**`** (shared Pkl/config modules the repo factors tasks into).
- The project's own `moon.*` and its local `.moon/tasks/**`.
- Configs may be `.yml`, `.pkl`, `.json`, `.toml`, `.hcl` — read whatever the repo uses,
  and **match that format and its conventions** when you add to it (don't drop a YAML
  file beside a project that defines everything in Pkl tag files).

**Then look for what already covers part of the request.** Existing tasks, `fileGroups`,
tags, and modules are the vocabulary you must reuse. If the repo already models `vite`
as its own task/module with a `vite-artifacts` fileGroup, a new clean **composes with
that** — it does not re-hardcode `dist/`/`node_modules/.vite` paths that something else
already owns.

### 2. Compose with what exists — don't wedge a duplicate
This is the lesson behind step 1. Once you know what's there, extend it in its own idiom:
- **Reuse fileGroups** (`@group(vite-artifacts)`) instead of re-listing paths.
- **`extends`** a sibling task, or add to the existing tag/module file, rather than
  creating a parallel one.
- **`deps`** onto an existing task so behaviour is shared, not copied. If a shared
  `vite-clean` (or equivalent) already exists, an `astro-clean` should *depend on or
  extend it*, not re-implement Vite's cache paths inside the astro tag.
- Only introduce a new standalone task when nothing existing covers the concern — and
  say so in your explanation, citing what you surveyed.

A duplicate that hardcodes knowledge already modelled elsewhere is a bug even if it
"works": it drifts the moment the original changes. Surveying first is how a competent
engineer avoids it — make it your default.

### 3. Discover the toolchain & its real outputs (cross-check against the survey)
The user rarely spells out build internals — **derive them**, then reconcile with what
the survey found:
- Read the project's `package.json` deps/scripts and framework config
  (`astro.config.*`, `vite.config.*`, `next.config.*`, `tsconfig.*`) to learn what it
  actually runs and emits.
- Chase the chain. An Astro app depends on `astro`, **which builds on Vite** — outputs
  land in `dist/` and `.astro/`, and Vite caches in `node_modules/.vite`. A real clean
  covers all three. Reach that from the dependencies, not from being told "Astro uses
  Vite." (Next→`.next/`, tsc→`*.tsbuildinfo`, etc.)
- If the survey already exposed these as a fileGroup or task, prefer that over your
  freshly-derived list — the repo's own model wins.

### 4. Worked example — compose, don't duplicate
Say the survey (steps 1–2) found the repo already models Vite as its own concern:
```
.moon/tasks/vite.yml         # fileGroup `vite-artifacts` = {dist,build}/**, vite-* tasks
src/web/.moon/tasks/tag-astro.pkl   # astro tasks, tag-scoped, Pkl
```
The wrong move (the real-world bug) is to bolt an `astro-clean` onto the astro tag that
hardcodes `rm -rf node_modules/.vite dist` — re-encoding paths the `vite` config already
owns. The right move is to put the **Vite-cache cleanup where Vite already lives** and
have astro compose with it.

```pkl
// .moon/tasks/vite.yml (or the vite module) — clean lives WITH the vite concern,
// reusing the existing fileGroup instead of re-listing paths
tasks:
  vite-clean:
    toolchains: ['system']      # no shell needed — rm is the command
    command: 'rm'
    args: ['-rf', 'node_modules/.vite']
    options:
      cache: false              # cleaning has no cacheable output
      runInCI: false
      os: ['linux', 'macos']
```
```pkl
// tag-astro.pkl — astro's clean handles ONLY astro's own artifacts and DEPENDS on the
// shared vite-clean, so one `moon run web:astro-clean` does both, no duplication
["astro-clean"] {
  toolchains = List("system")
  command = "rm"
  args = List("-rf", ".astro", "node_modules/.astro")
  deps = List("~:vite-clean")   // compose with the existing vite task
  options { cache = false; runInCI = false; os = List("linux", "macos") }
}
```
Note `command: 'rm'` + `toolchains: ['system']` is cleaner than `script: 'rm -rf …'` —
no shell parse, and it's how idiomatic moon cleanup tasks are written.

### 5. `command` vs `script`
- `command:` — a **single** executable + args (moon parses it). Prefer it; pair with
  `toolchains: ['system']` for plain binaries like `rm`.
- `script:` — a **shell line**; required for pipes, `&&`, `;`, or multiple commands.
  (v1 let you stuff shell strings into `command`; v2 rejects that — a common trap.
  `schemas/tasks.md` → `tasks.*.command` vs `tasks.*.script`.)

### 6. Sharing & inheritance mechanics
Global tasks live in **`.moon/tasks/**/*`** and are inherited via **`inheritedBy`**
(`toolchain`, `tag`, `layer`, `stack`, `language`). Define once, inherit everywhere.
Target scopes for `deps`:

| Target | Means |
|--------|-------|
| `app:build` | task `build` in project `app` |
| `~:vite-clean` or bare `vite-clean` | same (owning) project |
| `^:clean` | the same task in **all depended-on** projects |
| `:clean` | task `clean` in **all** projects |

> v1 used a single `.moon/tasks.yml`. v2 uses the **`.moon/tasks/` directory**. Emitting
> `.moon/tasks.yml` into a v2 repo is a classic mistake.

### 7. Merging when local meets inherited
A local task with the same name as an inherited one is **merged** (v2 deep-merges).
Control it with `options.merge*` (`append` default / `prepend` / `replace` / `preserve`)
per parameter (`mergeArgs`, `mergeDeps`, …). Reach for `replace` only to fully override.

### 8. Inputs/outputs (affected + caching)
`inputs` decide when a task is "affected" and re-runs; `outputs` are what gets cached.
A clean task wants `options.cache: false`; a build task wants real `outputs`. Reuse
existing `fileGroups` (`@group(vite-artifacts)`) rather than re-listing globs.

---

## Plugins, extensions & sharing config

- **Sharing across projects/repos** — the `extends` field (in `.moon/workspace.*`,
  `.moon/toolchains.*`, `.moon/extensions.*`, and `.moon/tasks/**/*`) takes an HTTPS URL
  or relative path to a config document. **Pin a tag/commit SHA** in the URL, never a
  moving branch, or upstream changes silently break builds. (`docs/guides/sharing-config.mdx`.)
- **Extensions** — registered in `.moon/extensions.*` (`schemas/extensions.md`);
  see `docs/config/extensions.mdx` and `docs/guides/extensions.mdx`.
- **WASM toolchain plugins** — v2 replaced hard-coded "platforms" with community WASM
  toolchains (Extism). For authoring or wiring one up, read `docs/guides/wasm-plugins.mdx`
  and `docs/concepts/toolchain.mdx`.

For Block65's reusable "common moon" config, model it as an upstream `extends` source
(a versioned `.moon/tasks/*.yml` set) plus shared tags — exactly the sharing-config
pattern above.

---

## Debugging

For a task that fails / is skipped / won't cache / re-runs every time, use the official
moon **`debug-task`** workflow, vendored into the cache so it's always at the same pinned
version as the docs:

- Read `cache/v2/debug-task/references/decision-tree.md` and follow it — it gives exact
  commands (`moon task <target> --json`, `moon hash <hash>`, `MOON_DEBUG_PROCESS_ENV=true
  moon run <target> --log trace --force`) for each branch.
- Companion references: `cache/v2/debug-task/references/{cache-issues,config-mistakes,environment-debug}.md`.
- If the user has it installed as a standalone skill (`npx skills add moonrepo/moon
  --skill debug-task`), prefer invoking that directly.

Debugging is config-correctness-adjacent: a "broken" task is often v1 syntax in a v2 repo
or a wrong `inheritedBy` condition — cross-check against `schemas/tasks.md` and
`config-mistakes.md`.

---

## Updating the knowledge base

One command refreshes everything from upstream; unchanged files are skipped via the SHA
manifest, so it's cheap to run often.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py"            # latest master, v2
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py" --ref v2.3.1   # pin a release
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py" --version v1   # build the frozen v1 tree
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py" --distill      # also LLM-distill prose into dense rules
python "${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/scripts/sync.py" --force        # ignore manifest, re-fetch all
```

`--distill` shells to a local CLI (`claude-cli` default; `gemini-cli`/`copilot-cli` via
`--provider`) — no API keys. Schemas are always rendered deterministically regardless;
distillation only compresses the prose docs for cheaper reads. The manifest records the
`ref` and `synced_at`, so `cat cache/v2/manifest.json` tells you how fresh the KB is.

---

## Paths — two kinds, don't confuse them

- **Shipped skill assets** (`scripts/sync.py`, `references/index.md`) live in this skill's
  directory — address them as `${CLAUDE_PLUGIN_ROOT}/skills/moonrepo/...` so they resolve
  whether installed as a plugin or standalone. Don't hunt for them with Explore.
- **Generated cache** (`schemas/`, `docs/`, `digests/`, `debug-task/`) is written once and
  shared across all repos at `~/.claude/skills/moonrepo/cache/<version>/`.

## Troubleshooting

- **Cache empty / page missing** → run `sync.py` (add `--force` to rebuild). Check
  `docs/_index.md` for the exact page path.
- **`${CLAUDE_PLUGIN_ROOT}` is empty** → you're outside the plugin runtime; substitute
  this skill's real directory in the commands above.
- **Field you "remember" isn't in `schemas/<file>.md`** → trust the schema, not memory;
  it's likely a v1 field or never existed.
- **Network blocked** → the cache is offline-usable once built; report rather than
  WebFetching raw docs into context.
- **No `pkl` binary but repo uses `.pkl` config** → moon needs `pkl` installed to read it
  (`proto install pkl` or the apple/pkl release); flag this to the user.
