---
name: github-issue
description: "Create and maintain GitHub issues from user reports and screenshots, fast and without over-investigating. CREATE: use when the user says 'log a GitHub issue', 'file a bug', 'raise an issue', 'open an issue', 'log this on GitHub', or pastes/attaches a screenshot of something broken and asks to report it — captures the symptom, works out steps to reproduce where possible, uploads any screenshot/video and embeds it, applies the GitHub issue authoring standard, and files immediately. UPDATE: use when the user says 'update the issue', 'add a comment to #N', 'attach this to the issue', 'edit the issue body', 'relabel', 'close/reopen the issue' — adds comments with media, edits the body, upgrades the repro provenance badge, relabels, and closes/reopens. It does NOT root-cause the code or prescribe a fix — that's for triage."
---

# Create & Maintain GitHub Issues

Turn a user report (text/screenshot) into a well-formed GitHub issue and maintain it — fast, no full code investigation. The fix is decided in triage, not here.

**Mode: act immediately.** Do not draft-and-confirm. For a new report: capture, badge, label, `gh issue create`, return the URL. For an update: make the change and report what changed.

## Project configuration

This skill is project-agnostic. Read the consuming project's `## GitHub Issues` block (in its `AGENTS.md` / `CLAUDE.md`) for:

- **Repo** — `<owner>/<repo>` to file against.
- **Labels** — the AI-filed label (e.g. `genai`), the `bug`/`enhancement` classifiers, and the `area/*` vocabulary.
- **Attachment upload** (optional) — a command (named in the config block) that takes a file and prints its public URL. If the project names none, transcribe media instead (see "Attaching files").

If a project has no such block, ask the user for the repo, use plain `bug`/`enhancement` labels, and transcribe rather than upload.

## The contract

Follow **`workflow/github-issues.md`** (the GitHub issue authoring standard): symptom-first, template fields only, ≤120 words (150 hard max), name file/service but not line numbers, one audience per issue, **never prescribe the fix**, provenance-tagged repro, badge row on top.

## How much to investigate

The goal is a *reproducible, well-scoped* report — not a diagnosis.

**Do (light triage):**
- Read the screenshot to ground the symptom in what's on screen.
- Work out **steps to reproduce** where possible — from the report, the screenshot, and obvious knowledge of the app's flows. A quick look at the relevant route/UI to confirm the repro path is fine.
- Identify the affected **surface/area** to pick the `area/*` label.
- If a root cause is genuinely obvious at a glance, note it as a single provisional `Likely:` line — never chase it.
- Note any factual **gap** you can see — no logging on the failing path, a missing validation, an unconsumed queue. Absence is a symptom (evidence), not a fix; don't omit it for fear it reads as prescriptive.

**Don't (the token waste to avoid):**
- No deep code spelunking, no tracing across files, no investigation sub-agents.
- No root-cause hunt, no diffs, no fix, no resolution menu, no acceptance criteria.
- Don't block on reproducing it. If steps can't be derived, say so in one line and file anyway.

## Steps

1. **Read the inputs.** The user's words + any screenshot (use Read on the image — it renders). Establish the single user-visible symptom.

2. **Steps to reproduce — tag provenance (required).** Start the field with one of `Reported by user:` / `Inferred (unconfirmed):` / `Not reproduced: <what's missing>`. Number the steps, minimal path (≤6). Never present inferred steps as reported.

3. **Write the body.** Start with the **badge row** (see the standard's Badges section), a blank line, then the template fields (bug shape — most reports are bugs):
   - **What happened** — the symptom. ≤40 words. No function/file name in the first sentence.
   - **Steps to reproduce** — from step 2, provenance tag first.
   - **Expected behaviour** — one sentence.
   - **Evidence** — embed any screenshot/file (see "Attaching files"), plus a one-line description and the affected file/service if known. Optional trailing `Likely: …` line only if the cause is obvious.

   For a capability gap use the enhancement shape: **Problem / motivation**, **Desired outcome**, **Alternatives** (only if a real trade-off exists).

4. **Pick labels** from project config: the AI-filed label + `bug`/`enhancement` + best-guess `area/*`. Don't investigate just to be sure of the area. If a configured label doesn't exist in the repo, create it (`gh label create`) or drop the unknown `area/*` and file anyway — never let a missing label block the create.

5. **Create it** (substitute the configured repo and labels):

   ```sh
   gh issue create --repo "$REPO" \
     --title "<area>: <symptom-first, specific>" \
     --body "<body from step 3>" \
     --label "$AI_LABEL" --label bug --label area/<surface>
   ```

   Title is symptom-first and specific. Never restate the title verbatim in the body's first line — the title is the terse label; the body opens with the fuller observed symptom.

6. **Return the issue URL.** Any screenshot is already embedded, so nothing is left for the user to do.

## Updating an existing issue

Same contract applies. **Always fetch current state first:**

```sh
gh issue view <n> --repo "$REPO" --json number,title,body,labels,state
```

**Comment vs edit:** add a **comment** for genuinely new information (a follow-up, extra evidence, a repro confirmation). **Edit the body** only to correct/upgrade what's there or to insert media. Editing must never delete a human's words.

- **Add a comment (+ media)** — upload any new screenshot/video and embed it.
  ```sh
  gh issue comment <n> --repo "$REPO" --body "<comment + embedded media>"
  ```
- **Edit the body (+ media)** — `gh issue edit --body` **replaces the entire body**, so fetch it first, modify in place, and pass the full new text.
  ```sh
  gh issue edit <n> --repo "$REPO" --body "<full modified body>"
  ```
- **Upgrade provenance** — when an inferred repro is confirmed: edit the body to swap the orange `repro: inferred` badge for green `repro: user-reported`, and change the Steps tag to `Reported by user:`. The main reason to edit rather than comment.
- **Relabel / triage** — `gh issue edit <n> --repo "$REPO" --add-label area/<x> --remove-label area/<y>`.
- **Close / reopen** — `gh issue close <n> --repo "$REPO" --reason completed` (or `not planned`); `gh issue reopen <n> --repo "$REPO"`.

## Attaching files (screenshots, screen recordings, logs, PDFs)

GitHub has no attachment API, so `gh` can't upload files. The upload is the **project's** responsibility — its config block names an upload command that takes a local file, uploads it under an unguessable key, and prints a public URL. The skill runs that command and turns the URL into markdown; if none is configured, transcribe the media into Evidence instead.

```sh
url="$(<the project's configured upload command> "$path")"   # prints the public URL
```

Embed the URL by file type:

- **image** → `![<name>](<url>)` (inline)
- **video** → `<video controls src="<url>"></video>` (inline player — GitHub allows `<video>`; image syntax does not work for video)
- **anything else** → `[<name>](<url>)` (download link)

Paste the result into the Evidence field (or a comment). (Camo caching and the unique-key rationale live in the standard's Attachments section — don't restate them here.)

## Output

Brief. On create: the issue URL, its title, and the labels applied. On update: the issue URL and one line on what changed. Don't recap the whole body.
