---
name: github-issue
description: "Create and maintain GitHub issues from user reports and screenshots, fast and without over-investigating. CREATE: use when the user says 'log a GitHub issue', 'file a bug', 'raise an issue', 'open an issue', 'log this on GitHub', or pastes/attaches a screenshot of something broken and asks to report it — captures the symptom, works out steps to reproduce where possible, uploads any screenshot/video and embeds it, applies the GitHub issue authoring standard, and files immediately. UPDATE: use when the user says 'update the issue', 'add a comment to #N', 'attach this to the issue', 'edit the issue body', 'relabel', 'close/reopen the issue' — adds comments with media, edits the body, upgrades the repro provenance badge, relabels, and closes/reopens. It does NOT root-cause the code or prescribe a fix — that's for triage."
---

# Create & Maintain GitHub Issues

Turn a user report (text and/or screenshot) into a well-formed GitHub issue, and keep it up to date afterwards — quickly, without burning tokens on a full code investigation. The fix is decided in triage, not here.

**Mode: act immediately.** Do not draft-and-confirm. For a new report: capture, badge, label, `gh issue create`, return the URL. For an update: make the change and report what changed.

## Project configuration

This skill is project-agnostic. Read the consuming project's `## GitHub Issues` block (in its `AGENTS.md` / `CLAUDE.md`) for:

- **Repo** — `<owner>/<repo>` to file against.
- **Labels** — the AI-filed label (e.g. `genai`), the `bug`/`enhancement` classifiers, and the `area/*` vocabulary.
- **Issue-asset store** (optional) — public bucket name, public base URL, key prefix, and upload command. If the project declares none, skip uploads and transcribe media instead (see "Attaching files").

If a project has no such block, ask the user for the repo, use plain `bug`/`enhancement` labels, and transcribe rather than upload.

## The contract

Follow **`workflow/github-issues.md`** (the GitHub issue authoring standard): symptom-first, template fields only, ≤120 words, name file/service but not line numbers, one audience per issue, **never prescribe the fix**, provenance-tagged repro, badge row on top.

## How much to investigate

The goal is a *reproducible, well-scoped* report — not a diagnosis.

**Do (light triage):**
- Read the screenshot to ground the symptom in what's on screen.
- Work out **steps to reproduce** where possible — from the report, the screenshot, and obvious knowledge of the app's flows. A quick look at the relevant route/UI to confirm the repro path is fine.
- Identify the affected **surface/area** to pick the `area/*` label.
- If a root cause is genuinely obvious at a glance, note it as a single provisional `Likely:` line — never chase it.

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

4. **Pick labels** from project config: the AI-filed label + `bug`/`enhancement` + best-guess `area/*`. Don't investigate just to be sure of the area.

5. **Create it** (substitute the configured repo and labels):

   ```sh
   gh issue create --repo "$REPO" \
     --title "<area>: <symptom-first, specific>" \
     --body "<body from step 3>" \
     --label "$AI_LABEL" --label bug --label area/<surface>
   ```

   Title is symptom-first and specific. Never restate the title in the body's first line.

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

GitHub has no attachment API, so `gh` can't upload files. If the project configures an issue-asset store, upload there and embed the returned markdown — images inline, videos as a `<video>` player, other files as links. If no store is configured, transcribe what the media shows into Evidence instead.

The public URL is download-only; uploads go through the store's authenticated CLI. GitHub proxies embedded images through its Camo cache (`camo.githubusercontent.com`) — expected and harmless; unique keys keep it from serving a stale image.

Set these from the project's `## GitHub Issues` config, then use the helper:

```sh
# From project config:
ISSUE_BUCKET="<bucket-name>"                 # e.g. acme-issue-assets
ISSUE_PUBLIC="<https://pub-xxxx.r2.dev>"     # public base URL of the bucket
ISSUE_PREFIX="github/<owner>/<repo>/"        # key namespace
ISSUE_PUT="<upload command>"                 # e.g. pnpm exec wrangler r2 object put

upload_issue_asset() {
  # $1 = path to any local file; prints ready-to-paste markdown.
  # The object key is the only access control on a public bucket — 256 bits of
  # randomness, never a filename/hash/sequential id.
  f="$1"
  base="$(basename "$f")"
  ext=""
  case "$base" in *.*) ext=".${base##*.}" ;; esac
  key="${ISSUE_PREFIX}$(openssl rand -hex 32)${ext}"
  ct="$(file -b --mime-type "$f" 2>/dev/null || echo application/octet-stream)"

  $ISSUE_PUT "${ISSUE_BUCKET}/${key}" --file="$f" --content-type="$ct" --remote >/dev/null

  url="${ISSUE_PUBLIC}/${key}"
  case "$ct" in
    image/*) printf '![%s](%s)\n' "$base" "$url" ;;                  # inline image
    video/*) printf '<video controls src="%s"></video>\n' "$url" ;;  # inline player
    *)       printf '[%s](%s)\n'  "$base" "$url" ;;                   # download link
  esac
}
```

Run `upload_issue_asset` per file, paste the printed markdown into the Evidence field (or a comment), then create/update the issue.

## Output

Brief. On create: the issue URL, its title, and the labels applied. On update: the issue URL and one line on what changed. Don't recap the whole body.
