# TRIPLE — Three-Role Iterative Peer Loop Engineering

Also load: `workflow/git.md`, `workflow/communication.md`

A peer programming workflow where an implementation agent and a review agent
collaborate with a human throughout development. The PR is a merge mechanism,
not a review forum — it must be approved and green before it is opened.

## Roles

- **Human** — selects tasks, approves plans, triggers reviews, opens PRs, approves merges
- **Impl agent** — implements, runs quality checks, requests review, then revises, commits, pushes
- **Review agent** — reads files and git only; outputs a numbered list of findings, each with a file/line reference and a concise explanation; ends with exactly one of: `LGTM` or `Needs fixes`; does not run tests, build, or modify code

## Phases

### 1. Plan

Human and impl agent define scope. Output is a **TASK.md** (local only — never committed, never pushed):

```markdown
# <short descriptive title>

## Scope
<high-level area of the codebase — not a file list>

## Out of scope
<what not to touch>

## Why
<motivation — what problem does this solve>

## Notes
<optional — specific constraints or context>
```

Human approves TASK.md before any code is written.

### 2. Branch

Create a branch from `main` before writing any code. Do not implement on `main`. Branch name follows `<type>/<short-slug>`.

### 3. Implement → Review → Commit

Repeat as many times as needed:

1. Implement a logical unit
2. Run all quality checks and fix all failures
3. Human invokes the review agent — it reviews the working tree diff against `main`
4. Address all findings, loop back to 2
5. Once the review agent has no findings, human reviews
6. Human satisfied → commit

The impl agent must not commit autonomously. Never commit unreviewed code. Never commit a broken or partial state.
