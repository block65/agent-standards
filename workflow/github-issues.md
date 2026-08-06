# GitHub Issue Authoring

An issue states a **problem**; the **fix is decided in triage**, not in the issue. Write for the developer who picks it up. Keep it terse; AI-authored issues tend to sprawl.

Project specifics (target repo, issue types, label vocabulary, attachment upload) are configured per project — see the consuming project's `## GitHub Issues` block. The `github-issue` skill automates create/update against this standard.

## Structure

Fill the project's issue-template fields — never invent sections (`## Mechanism`, `## Fix`, `## Acceptance criteria`). Canonical field set:

- **bug** → *What happened* (symptom) · *Steps to reproduce* (tag provenance) · *Expected behaviour* · *Evidence*
- **enhancement** → *Problem / motivation* · *Desired outcome* (behaviour, not implementation) · *Alternatives* (only if a real trade-off exists)

The shape is the issue **Type** — a first-class GitHub field set with `gh issue create --type Bug` (or `--type Enhancement`), **not** a `bug`/`enhancement` label. It picks the field set above. A project may define other types (e.g. `Task`); follow its field set for those.

Agents usually create via `gh issue create --body`, which bypasses the web-UI template — so reproduce these as the body headings.

## Open with the symptom

First sentence = what a user/reader observes going wrong — the fuller symptom, not a verbatim echo of the symptom-first title. If it contains a `camelCase` identifier or a filename, restate the symptom first. Mechanism, if genuinely known, is one provisional line prefixed `Likely:` at the end — never a section, never manufactured.

## Never prescribe the fix

Banned: `Fix`/`Resolution`/`Approach` sections, "resolution is one of A/B/C" menus, naming a dependency/API to adopt, acceptance criteria or "tests first" deliverables, diffs, "in working tree pending commit". Allowed: the one-line `Likely:` root-cause lead, and naming the affected file/service/component/route. For enhancements, describe the desired outcome (behaviour), not the implementation.

A statement of fact is not a fix suggestion. Saying what's absent — "the DLQ has no consumer", "there's no logging on the failing path", "the entrypoint is missing the SDK's receiver-side wrapper" — is evidence, even when it names the API or instrumentation that's absent; state it plainly. Missing instrumentation (no logs, metrics, or trace on the path that failed) is itself a diagnostic symptom worth recording. The line is crossed only when the issue tells the developer what to *do* about it. Never omit a real gap for fear it reads as a fix — understating the symptom is the worse error.

## Detail level

Name the file/service — never line numbers (they rot). Internals (function names, constants) only inside the `Likely:` line, never in the opening symptom.

## Tag the repro's provenance — always

Triage must know whether the steps are trustworthy. Start *Steps to reproduce* with one of:

- `Reported by user:` — the steps came from the reporter. Trust as-is.
- `Inferred (unconfirmed):` — derived, not confirmed against the real failure.
- `Not reproduced: <what's missing>` — no steps; file anyway, don't invent them.

Never present inferred steps as if the user gave them.

## One audience per issue

`bug` → developer/triager; `enhancement` → the affected user/customer. The customer "why" is one impact sentence inside the first field, not a `## What the customer wants` wrapper around internals.

## Length

~60–120 words of prose, 150 hard max — the body only. Badge markdown, field headings, code spans and URLs don't count; measure the sentences a developer reads. Never include: CI/test results, bisect SHAs, self-referential meta-commentary, or a restatement of the title. Follow `writing/base.md`.

The budget constrains the body, not the issue. Overflow goes in a comment (below), never into a compressed body that drops verified evidence. If trimming means losing a finding, stop trimming.

## Comments carry the depth

The body is the triage-facing symptom report: what's broken, how to reproduce it, and the minimum evidence that makes the claim actionable. Everything else goes in a comment posted immediately after filing.

Belongs in a comment:

- **Full verification data** — the tables, byte counts, response headers, URL sweeps and command output behind the body's summary. Don't restate it in both; the body keeps the one number that makes the case, the comment holds the working.
- **Line numbers**, which the body may not carry. Pin them to a commit SHA and name the function or symbol as the durable anchor, since the numbers rot and the symbol doesn't.
- **Adjacent findings** turned up while investigating that aren't this bug. Say why each is out of scope and what it should become instead (a `Task`, its own bug, a product decision). Recording them beats losing them; merging them into the body is scope creep.

A comment is not a loophole. More evidence for the same problem belongs in a comment; a second problem gets its own issue. If the body's *symptom* sentence has to cover two unrelated failures, splitting is the answer, not a longer comment.

The rules that still apply in comments: never prescribe the fix, and follow `writing/base.md`.

## Badges (AI-authored issues)

When an agent files the issue, open the body with a one-line badge row so a developer sees provenance at a glance. Keep the alt text descriptive — it shows if shields.io fails to load.

- AI-filed: `![AI-filed](https://img.shields.io/badge/AI--filed-genai-blueviolet)`
- One repro badge, matching the provenance tag:

  | Provenance | Badge markdown |
  |---|---|
  | Reported by user | `![repro: user-reported](https://img.shields.io/badge/repro-user--reported-brightgreen)` |
  | Inferred (unconfirmed) | `![repro: inferred](https://img.shields.io/badge/repro-inferred-orange)` |
  | Not reproduced | `![repro: not reproduced](https://img.shields.io/badge/repro-not_reproduced-red)` |

Both badges on one line, then a blank line before the first field. When an inferred repro is later confirmed, edit the body to swap the orange badge for green and update the provenance tag.

## Attachments

GitHub has no attachment API. Host the file in the project's public object store and embed the URL in the body:

- **Images** inline: `![alt](url)`
- **Videos**: `<video controls src="url"></video>` renders a player only when the src is a GitHub upload (`user-attachments`, added via the web UI); the sanitizer strips `<video>` with any other host, so link externally hosted video like any other file
- **Everything else** (PDF, logs, zips) as a link: `[name](url)`

The project uploads under an unguessable key (256-bit random — on a public-readable, not writable, bucket the key is the only access control) and prints the URL. The `github-issue` skill calls it and embeds the URL. Unique keys stop GitHub's Camo cache serving stale images.
