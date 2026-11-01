# GitHub Issue Authoring

An issue states a **problem** for the developer who picks it up; the **fix is
decided in triage**. Follow [Writing (Base)](../writing/base.md) in the body and
in comments.

Project specifics (target repo, issue types, label vocabulary, attachment
upload) live in the consuming project's `## GitHub Issues` block. The
`github-issue` skill automates create/update against this standard.

## Structure

Use only the project's issue-template fields, never invented sections
(`## Mechanism`, `## Fix`, `## Acceptance criteria`). Canonical field set:

- **bug** → _What happened_ (symptom) · _Steps to reproduce_ (tag provenance) ·
  _Expected behaviour_ · _Evidence_
- **enhancement** → _Problem / motivation_ · _Desired outcome_ (behaviour, not
  implementation) · _Alternatives_ (only if a real trade-off exists)
- **task** → _Task_ (what to do, as numbered steps when there are several) ·
  _Done when_ (the observable result)

The shape is the issue **Type**, set with `gh issue create --type Bug` (or
`--type Enhancement`), not a `bug`/`enhancement` label. Follow the field set of
any other type the project defines (e.g. `Task`). `gh issue create --body`
bypasses the web-UI template, so write these fields as the body headings.

## Title: the working outcome

A developer reads the title alone, in a list, and knows what it is, roughly why
it happens and how big it is, without opening the body. When the issue closes,
the title reads as what people now have. State the behaviour that should hold,
in the product's words: a fix is the side effect of wanting working behaviour,
as a green test is of correct code. Leave out an area prefix (the label carries
it), the mechanism, and an environment qualifier unless the problem exists only
there.

- **Bug**: what should be true, the fix in plain words, or the plain problem a
  user meets.
  - BAD: "[Component] throws on [Condition] in [Function] on production"
  - GOOD: "[Pages] should not error or redirect if [Input] fails validation"
  - GOOD: "Unable to drag to reorder [Items] in [Surface]"
- **Feature**: "Allow [who] to [do what] [where]" for a capability people use,
  or "Add [thing] to [place]" when the value lies elsewhere (SEO, analytics)
  and the title just names the work.
  - BAD: "[Actor] cannot [Action]"
  - BAD: "[Page] offers no [jargon for the missing thing]" (a feature described
    by reporting its absence)
  - GOOD: "Allow deactivation of [Record]s via [Surface]"
  - GOOD: "Add popular searches links to the search hero in [Page]"
- **Task**: an outcome verb first (Ensure, Investigate and verify, Confirm),
  detail in brackets.
  - BAD: "[Worker]'s [Messages] never reach [Consumer] in dev"
  - GOOD: "Ensure [Messages] are delivered in dev"

## One job per issue

An issue is one job with one "done". It closes when the commit that delivers it
reaches the default branch, whatever has been deployed. Follow-on scope, a
separate open question, and a chore someone does by hand (configuring a
third-party webhook, rotating a secret) are new linked issues, never additions
to this one. An issue that grows until nothing can close it reads to a client
as work never done.

Before adding to an open issue, check whether the addition changes what "done"
means; if it does, file a new issue and link it. Fold decisions into the body as
the current truth, never a dated log. An open issue whose fix is already on the
default branch closes, with any remainder split out first.

## Open with the symptom

The first sentence is what a user or reader observes going wrong: the fuller
symptom, not an echo of the title, and free of `camelCase`
identifiers and filenames. A mechanism, if genuinely known, is one provisional
line prefixed `Likely:` at the end, never a section and never manufactured.

## Never prescribe the fix

Leave out `Fix`/`Resolution`/`Approach` sections, "resolution is one of A/B/C"
menus, a dependency or API to adopt, acceptance criteria or "tests first"
deliverables, diffs, and "in working tree pending commit". The ban binds
sentences, not headings: a build plan under _Desired outcome_ is still a fix.
Its tells are comparative-cost framing ("cheapest/simplest shape would be"),
precedent to copy ("there is precedent in [File]"), and costing the work ("it
would need [Credential] as a repo secret"). Allowed: the `Likely:` line, and
naming the affected service, component or route. For an enhancement, describe
the desired behaviour.

A statement of fact is not a fix. Absence on the failing path is evidence, and
missing instrumentation there (no log, metric or trace) is itself a symptom:
state it, even where naming the gap names an API. The line is crossed when the
issue says what to _do_ about it. Report every real gap: understating the
symptom is a worse error than reading like a fix.
This licence covers the failing path only; framing every other fact as a lack is
the register defect below.

## State the present, positively, in concrete nouns

The body is read once, by someone who was not in the investigation. Six habits
write to the author's train of thought instead.

- **A negation must carry information.** It earns its place when the missing
  thing sits on the failing path and its absence is the symptom; test each one
  rather than counting them. Otherwise use the positive form, and drop invented
  contrast per [Communication](communication.md).
  - BAD: "Nothing tells [Service] when a [Record] changes."
  - GOOD: "[Record] publishes without notifying [Service]."
- **No corrections.** When a finding changes, edit the body to the current
  truth, with no appended revision, `(corrected)` label, or parenthesis
  explaining why a line is present. The reader never held the earlier belief.
  - BAD: "The degradation is narrower than first described. The trigger is
    [Condition], not [Other]."
  - GOOD: "[Condition] triggers [Symptom]."
- **Concrete nouns, no rankings.** Each sentence names the observable thing: the
  response, the record, the screen. Category nouns ("a good value") and rankings
  ("the primary realistic trigger") claim something the reader cannot check.
  - BAD: "The primary realistic trigger is a [Scope] that has never had a good
    value."
  - GOOD: "A new [Scope] with no [Record] serves an empty [Component]."
- **Report, never steer.** Supply the evidence and leave the weighing to triage:
  cut "weigh that against", "defensible", "worth recording", and every sentence
  arguing the issue's own importance. How the failure was found belongs in the
  repro tag only.
  - BAD: "Weigh that against the failure running undetected for months, found by
    accident via an unrelated [Test]."
  - GOOD: "[Symptom] was present in production for [Duration]."
- **No narrator.** Write flat statements about the system, with no "I" or "we"
  and no verdict on the report's own contents.
  - BAD: "The part I would question is [Design], since it [Consequence]."
  - GOOD: "[Design] puts [Cost] on [Path]."
- **No coined vocabulary.** Use the words the product and codebase already use,
  or describe the thing.
  - BAD: "Recorded here as the main path, not a footnote."
  - GOOD: "Every [Surface] in a new [Scope] shows [Symptom]."

## Detail level

Name the affected service, route or user-facing surface. Filenames, paths,
functions and constants go in the SHA-pinned comment, since they rot. The
`Likely:` line may carry one symbol where the mechanism turns on it.

## Tag the repro's provenance, always

Start _Steps to reproduce_ with one of:

- `Reported by user:`: the steps came from the reporter. Trust as-is.
- `Inferred (unconfirmed):`: derived, not confirmed against the real failure.
  Never present these as the user's.
- `Not reproduced: <what's missing>`: no steps; file anyway, without inventing
  them.

## One audience per issue

`bug` → developer/triager; `enhancement` → the affected user/customer. The
customer "why" is one impact sentence inside the first field, not a
`## What the customer wants` wrapper around internals.

## Body and comments

The body holds the sentences a triager reads to act: the symptom, the repro, and
the minimum evidence behind them. Leave out CI/test results, bisect SHAs,
meta-commentary, and a restatement of the title. Post everything else as a
comment immediately after filing, rather than compressing the body until a
verified finding drops out:

- **Full verification data**: the tables, byte counts, headers, URL sweeps and
  command output. The body keeps the one number that makes the case.
- **Line numbers, filenames and symbols**, pinned to a commit SHA, with the
  function or symbol named as the durable anchor.
- **Adjacent findings** that aren't this bug, each with why it is out of scope
  and what it should become (a `Task`, its own bug, a product decision).

A second problem gets its own issue, not a comment: if the symptom sentence has
to cover two unrelated failures, split. The fix ban applies in comments too.

## Badges (AI-authored issues)

When an agent files the issue, open the body with a one-line badge row. Keep the
alt text descriptive; it shows if shields.io fails to load.

- AI-filed:
  `![AI-filed](https://img.shields.io/badge/AI--filed-genai-blueviolet)`
- One repro badge, matching the provenance tag:

  | Provenance             | Badge markdown                                                                           |
  | ---------------------- | ---------------------------------------------------------------------------------------- |
  | Reported by user       | `![repro: user-reported](https://img.shields.io/badge/repro-user--reported-brightgreen)` |
  | Inferred (unconfirmed) | `![repro: inferred](https://img.shields.io/badge/repro-inferred-orange)`                 |
  | Not reproduced         | `![repro: not reproduced](https://img.shields.io/badge/repro-not_reproduced-red)`        |

Both badges on one line, then a blank line before the first field. When an
inferred repro is later confirmed, swap the orange badge for green and update
the provenance tag.

## Attachments

GitHub has no attachment API. Host the file in the project's public object store
and embed the URL:

- **Images** inline: `![alt](url)`
- **Videos**: `<video controls src="url"></video>` renders only when the src is
  a GitHub upload (`user-attachments`); the sanitizer strips `<video>` with any
  other host, so link externally hosted video like any other file
- **Everything else** (PDF, logs, zips) as a link: `[name](url)`

The project's upload command stores the file under an unguessable key (256-bit
random; on a public-readable, not writable, bucket the key is the only access
control) and prints the URL. Unique keys also stop GitHub's Camo cache serving
stale images.
