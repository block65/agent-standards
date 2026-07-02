# GitHub Issue Authoring

An issue states a **problem**; the **fix is decided in triage**, not in the issue. Write for the developer who picks it up. Keep it terse — these rules exist because AI-authored issues tend to sprawl.

Project specifics (target repo, label vocabulary, issue-asset store) are configured per project — see the consuming project's `## GitHub Issues` block. The `github-issue` skill automates create/update against this standard.

## Structure

Fill the project's issue-template fields — never invent sections (`## Mechanism`, `## Fix`, `## Acceptance criteria`). Canonical field set:

- **bug** → *What happened* (symptom) · *Steps to reproduce* (tag provenance) · *Expected behaviour* · *Evidence*
- **enhancement** → *Problem / motivation* · *Desired outcome* (behaviour, not implementation) · *Alternatives* (only if a real trade-off exists)

Agents usually create via `gh issue create --body`, which bypasses the web-UI template — so reproduce these as the body headings.

## Open with the symptom

First sentence = what a user/reader observes going wrong. If it contains a `camelCase` identifier or a filename, restate the symptom first. Mechanism, if genuinely known, is one provisional line prefixed `Likely:` at the end — never a section, never manufactured.

## Never prescribe the fix

Banned: `Fix`/`Resolution`/`Approach` sections, "resolution is one of A/B/C" menus, naming a dependency/API to adopt, acceptance criteria or "tests first" deliverables, diffs, "in working tree pending commit". Allowed: the one-line `Likely:` root-cause lead, and naming the affected file/service/component/route. For enhancements, describe the desired outcome (behaviour), not the implementation.

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

~60–120 words, 150 hard max. Never include: CI/test results, bisect SHAs, self-referential meta-commentary, or a restatement of the title. Follow `writing/base.md`.

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
- **Videos** as a player: `<video controls src="url"></video>` (GitHub's markdown sanitizer allows `<video>`; image syntax does not work for video)
- **Everything else** (PDF, logs, zips) as a link: `[name](url)`

The upload is the project's responsibility — by convention a `just issue-asset <file>` recipe that uploads under an unguessable key (256-bit random; on a public bucket the key is the only access control) and prints the public URL. The `github-issue` skill calls it and embeds the URL. GitHub proxies embedded images through its Camo cache; unique keys keep that cache from ever serving a stale image.
