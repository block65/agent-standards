---
name: handover
description: Wrap up the current session into a complete handover prompt a fresh agent can run with, save it to a file, and copy it to the clipboard so the user can /clear and paste. Use this skill whenever the user says "handover", "hand over to a new agent", "let's handover", "prepare a handoff", "wrap this up for a new session", "I'm going to clear", or otherwise wants to continue this work in a fresh context without losing progress — even if they don't use the word "handover". Accepts an optional steering instruction after the trigger (like /compact takes one), e.g. "handover — just the dragon-hatchery work" or "handover, have the next agent start with the potion tests".
---

# Handover

Produce a handover prompt: a single self-contained brief that lets a brand-new agent session continue this work as if it had been here all along. Save it to a file, copy it to the clipboard, and tell the user they can `/clear` and paste.

The one rule that matters: **the new agent knows nothing.** It has not seen this conversation, your tool results, or your reasoning. Anything not written into the handover is lost — every hard-won fact, every dead end, every quirk of the environment. Write the brief for a smart stranger, not for yourself.

## Steering

The user may attach an instruction to the handover request, the way `/compact` takes one — anything after the trigger phrase or passed as args is steering, not part of the task. Honor it as a directive about the brief itself:

(The examples below are deliberately fantastical so they can't be mistaken for real session content.)

- **Scope**: "just the dragon-hatchery work" — cover only that thread; drop the others entirely rather than summarising them ("we also polished the castle CSS" is noise to an agent scoped away from it). If a dropped thread left the working tree dirty, still note that under "Where things stand" so the next agent isn't surprised by unexplained changes.
- **Redirection**: "have the next agent start with the potion tests" — this rewrites Next steps and Start here. The user is changing the plan at handover time; the brief reflects the new plan, not the session's old one.
- **Emphasis or form**: "keep it short", "include the full scrying-mirror error output" — adjust accordingly.

If the steering contradicts what you believe the state to be (e.g. "say the wyvern API is done" when you never verified it), keep the brief truthful: follow the user's framing but preserve the verification caveat. A misleading handover defeats the whole exercise.

With no steering, cover everything in the session at your own judgment.

## Step 1 — Take stock

Before writing anything, gather the ground truth. Do not rely on memory of the conversation alone — verify the current state:

- `git status` and `git log --oneline -10` (if in a repo): branch, uncommitted changes, recent commits made this session
- The original request: what did the user actually ask for, in their words? Include follow-up corrections they made along the way — those are requirements too.
- What is **done** — only things you verified (tests passed, command ran, commit exists). If you believe something works but never checked, say so plainly in the brief.
- What is **in progress** — the exact half-finished state: which file, what's written so far, what remains. This is the most valuable and most perishable information; be precise.
- What is **next** — the remaining steps, in order, as concretely as you can state them.
- **Hints and gotchas** — everything the next agent would otherwise have to rediscover: the exact build/test/run commands that work here, environment quirks, decisions the user made ("no new dependencies", "use X not Y"), and dead ends already tried with why they failed. Dead ends are pure gold: they save the next agent from burning time repeating them.

## Step 2 — Write the handover file

Write the brief to `~/.claude/handovers/<project-dir-name>-<YYYYMMDD-HHMMSS>.md` (create the directory with `mkdir -p` if needed; get the timestamp from `date +%Y%m%d-%H%M%S`).

Use this structure — it is a prompt addressed to the next agent, so write in the imperative, second person:

```markdown
You are taking over an in-progress task from a previous agent session. That session's
context is gone; this brief is everything. Do not assume knowledge beyond what is here.

# Task
<One short paragraph: what the user wants and why. Their acceptance criteria, in their terms.>

# Where things stand
- Working directory: <absolute path>
- Branch: <branch> (branched from <base>)
- Uncommitted changes: <one-line summary, or "none">

## Done (verified)
- <fact — with its evidence: commit hash, test that passed, file that exists>

## In progress
- <the half-finished thing: file, current state, exactly what remains>

## Next steps (in order)
1. <step>
2. <step>

# Hints and gotchas
- Build/test/run: <the exact commands that work in this project>
- <user decisions and constraints stated during the session>
- <dead ends already tried, and why they failed>
- <environment quirks>

# Key files
- <absolute path> — <why it matters>

# Start here
1. <a command to verify the state described above, e.g. run the tests>
2. <then continue with next step 1>
```

Quality bar for the brief:

- **Absolute paths everywhere.** The next agent may resolve relative paths differently.
- **No code dumps.** Point at files; the next agent can read them. The brief should stay well under ~150 lines — a wall of text gets skimmed, and skimming loses facts.
- **No conversational references.** "As discussed above" and "the earlier approach" mean nothing to a reader who wasn't there. Restate the fact itself.
- **Claims carry evidence.** "Tests pass" is weaker than "`pnpm test` passed (42 tests) after the last edit to foo.ts". If the next agent can re-verify a claim cheaply, tell it how.
- **State uncertainty plainly.** If something is unverified or you suspect a problem, say so. A wrong "done" costs the next agent far more than "probably done, verify with X".

## Step 3 — Copy to clipboard

Run the bundled script with the file you just wrote:

```bash
bash <skill-dir>/scripts/copy-to-clipboard.sh ~/.claude/handovers/<file>.md
```

It auto-detects the available clipboard tool (wl-copy, xclip, xsel, pbcopy). If it exits non-zero, no clipboard tool exists — don't try to install one; just tell the user the file path so they can copy it themselves.

## Step 4 — Hand back to the user

Close with a short confirmation, nothing more — the handover file is the deliverable, so don't re-summarise its contents here. Tell the user:

- the handover is on the clipboard, and the backup file path
- next move is theirs: `/clear` (or open a new session), paste, go

Do not start any new work after this point — the session is ending.
