# GitHub Issue Authoring

An issue states a **problem**; the **fix is decided in triage**, not in the issue. Write for the developer who picks it up. Keep it terse; AI-authored issues tend to sprawl.

Project specifics (target repo, issue types, label vocabulary, attachment upload) are configured per project; see the consuming project's `## GitHub Issues` block. The `github-issue` skill automates create/update against this standard.

## Structure

Fill the project's issue-template fields, and never invent sections (`## Mechanism`, `## Fix`, `## Acceptance criteria`). Canonical field set:

- **bug** → _What happened_ (symptom) · _Steps to reproduce_ (tag provenance) · _Expected behaviour_ · _Evidence_
- **enhancement** → _Problem / motivation_ · _Desired outcome_ (behaviour, not implementation) · _Alternatives_ (only if a real trade-off exists)

The shape is the issue **Type**, a first-class GitHub field set with `gh issue create --type Bug` (or `--type Enhancement`), **not** a `bug`/`enhancement` label. It picks the field set above. A project may define other types (e.g. `Task`); follow its field set for those.

Agents usually create via `gh issue create --body`, which bypasses the web-UI template, so reproduce these as the body headings.

## Open with the symptom

First sentence = what a user/reader observes going wrong: the fuller symptom, not a verbatim echo of the symptom-first title. If it contains a `camelCase` identifier or a filename, restate the symptom first. Mechanism, if genuinely known, is one provisional line prefixed `Likely:` at the end, never a section and never manufactured.

## Never prescribe the fix

Banned: `Fix`/`Resolution`/`Approach` sections, "resolution is one of A/B/C" menus, naming a dependency/API to adopt, acceptance criteria or "tests first" deliverables, diffs, "in working tree pending commit". The ban binds sentences, not headings: a build plan under _Desired outcome_ is still a fix. Its tells are comparative-cost framing ("cheapest/simplest shape would be"), precedent to copy ("there is precedent in [File]"), and costing the work ("it would need [Credential] as a repo secret"). Allowed: the one-line `Likely:` root-cause lead, and naming the affected service/component/route. For enhancements, describe the desired outcome (behaviour), not the implementation.

A statement of fact is not a fix suggestion. Absence on the path that failed is evidence, and missing instrumentation there (no log, metric or trace) is itself a symptom: state it plainly, even where naming the gap names an API. The line is crossed when the issue says what to _do_ about it. Never omit a real gap for fear it reads as a fix; understating the symptom is the worse error. This licence covers the failing path. Framing every other fact as a lack is the register defect below, not evidence.

## State the present, positively, in concrete nouns

The body is read once, by someone who was not in the investigation. Six habits write to the author's train of thought instead.

- BAD: "I investigated this thoroughly and concluded that the paint is black, not white. And it matters."
- GOOD: "The paint is black."

- **A negation must carry information.** It earns its place when the missing thing sits on the failing path and its absence is the symptom. Where the issue never asserts X, "not X" answers a question nobody asked. Default to the positive form. A body about an absent thing will carry several licensed negations, so test each one rather than counting them. The contrastive form fails the same test: "X rather than Y", "not Y but X" and "X, never Y" assert Y so they can deny it, so where nothing proposed Y, state X alone.
  - BAD: "Nothing tells [Service] when a [Record] changes."
  - GOOD: "[Record] publishes without notifying [Service]."
- **No corrections.** The body states what is true now. When a finding changes, edit the body to the current truth. Never append the revision, label the seam `(corrected)`, or explain in parentheses why a line is present: the reader never held the belief being corrected.
  - BAD: "The degradation is narrower than first described. The trigger is [Condition], not [Other]."
  - GOOD: "[Condition] triggers [Symptom]."
- **Concrete nouns, no rankings.** Each sentence names the observable thing: the response, the record, the screen. Category nouns ("a good value") and rankings ("the primary realistic trigger") claim something the reader cannot check, against a set the issue never lists.
  - BAD: "The primary realistic trigger is a [Scope] that has never had a good value."
  - GOOD: "A new [Scope] with no [Record] serves an empty [Component]."
- **Report, never steer.** Triage weighs the evidence; the body supplies it. Cut "weigh that against", "defensible", "worth recording", and every sentence arguing the issue's own importance. How the failure was found is not the failure: provenance is the repro tag, and the rest is a story.
  - BAD: "Weigh that against the failure running undetected for months, found by accident via an unrelated [Test]."
  - GOOD: "[Symptom] was present in production for [Duration]."
- **No narrator.** The body carries no author voice: no "I" or "we", no hedged reaction ("I would question", "arguably", "to be fair"), no verdict on the report's own contents. A support agent or developer logging a job writes flat statements about the system; write those.
  - BAD: "The part I would question is [Design], since it [Consequence]."
  - GOOD: "[Design] puts [Cost] on [Path]."
- **No coined vocabulary.** Use the words the product and codebase already use, or describe the thing. A term minted in the body asks the reader to know a taxonomy that exists in this issue and nowhere else.
  - BAD: "Recorded here as the main path, not a footnote."
  - GOOD: "Every [Surface] in a new [Scope] shows [Symptom]."

## Detail level

Name the affected service, route or user-facing surface. Filenames, paths, functions and constants go in the follow-up comment pinned to a SHA, never in the body: they rot as line numbers do, only slower, and a body full of dead paths is unreadable long before it is wrong. The `Likely:` line may carry one symbol where the mechanism turns on it.

## Tag the repro's provenance, always

Triage must know whether the steps are trustworthy. Start _Steps to reproduce_ with one of:

- `Reported by user:`: the steps came from the reporter. Trust as-is.
- `Inferred (unconfirmed):`: derived, not confirmed against the real failure.
- `Not reproduced: <what's missing>`: no steps; file anyway, don't invent them.

Never present inferred steps as if the user gave them.

## One audience per issue

`bug` → developer/triager; `enhancement` → the affected user/customer. The customer "why" is one impact sentence inside the first field, not a `## What the customer wants` wrapper around internals.

## Length

~60–120 words of prose, 150 hard max, counting the body only. Badge markdown, field headings, code spans and URLs don't count; measure the sentences a developer reads. Never include: CI/test results, bisect SHAs, self-referential meta-commentary, or a restatement of the title. Follow `writing/base.md`.

The budget constrains the body, not the issue. Overflow goes in a comment (below), never into a compressed body that drops verified evidence. If trimming means losing a finding, stop trimming.

## Comments carry the depth

The body is the triage-facing symptom report: what's broken, how to reproduce it, and the minimum evidence that makes the claim actionable. Everything else goes in a comment posted immediately after filing.

Belongs in a comment:

- **Full verification data**: the tables, byte counts, response headers, URL sweeps and command output behind the body's summary. Don't restate it in both; the body keeps the one number that makes the case, the comment holds the working.
- **Line numbers, filenames and symbols**, which the body may not carry. Pin them to a commit SHA and name the function or symbol as the durable anchor, since the numbers rot and the symbol doesn't.
- **Adjacent findings** turned up while investigating that aren't this bug. Say why each is out of scope and what it should become instead (a `Task`, its own bug, a product decision). Recording them beats losing them; merging them into the body is scope creep.

A comment is not a loophole. More evidence for the same problem belongs in a comment; a second problem gets its own issue. If the body's _symptom_ sentence has to cover two unrelated failures, splitting is the answer, not a longer comment.

The rules that still apply in comments: never prescribe the fix, and follow `writing/base.md`.

## Badges (AI-authored issues)

When an agent files the issue, open the body with a one-line badge row so a developer sees provenance at a glance. Keep the alt text descriptive; it shows if shields.io fails to load.

- AI-filed: `![AI-filed](https://img.shields.io/badge/AI--filed-genai-blueviolet)`
- One repro badge, matching the provenance tag:

  | Provenance             | Badge markdown                                                                           |
  | ---------------------- | ---------------------------------------------------------------------------------------- |
  | Reported by user       | `![repro: user-reported](https://img.shields.io/badge/repro-user--reported-brightgreen)` |
  | Inferred (unconfirmed) | `![repro: inferred](https://img.shields.io/badge/repro-inferred-orange)`                 |
  | Not reproduced         | `![repro: not reproduced](https://img.shields.io/badge/repro-not_reproduced-red)`        |

Both badges on one line, then a blank line before the first field. When an inferred repro is later confirmed, edit the body to swap the orange badge for green and update the provenance tag.

## Attachments

GitHub has no attachment API. Host the file in the project's public object store and embed the URL in the body:

- **Images** inline: `![alt](url)`
- **Videos**: `<video controls src="url"></video>` renders a player only when the src is a GitHub upload (`user-attachments`, added via the web UI); the sanitizer strips `<video>` with any other host, so link externally hosted video like any other file
- **Everything else** (PDF, logs, zips) as a link: `[name](url)`

The project uploads under an unguessable key (256-bit random; on a public-readable, not writable, bucket the key is the only access control) and prints the URL. The `github-issue` skill calls it and embeds the URL. Unique keys stop GitHub's Camo cache serving stale images.
