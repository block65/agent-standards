import type { Hook, Register } from "claude-code";

// /recycle and /handover restart the Claude session in this tmux pane, carrying
// the conversation forward. The old session's model never gets a turn: the
// commands answer for themselves. The new session is a plain `claude` typed
// into the pane's own login shell, so it gets the user's environment however
// their shell is set up; it finds what was carried in the store, by pane.

const quote = (s: string) => `'${s.replaceAll("'", `'\\''`)}'`;

// How long a carried context waits for its pane's new session.
const PENDING_MS = 2 * 60 * 1000;
// Haiku bills a prompt past 100K tokens at five times the rate.
const HANDOVER_CHARS = 350_000;
const TAIL_CHARS = 30_000;
const FIRST_CHARS = 1_500;

type Pending = { at: number; context: string; kick: string };

const pendingKey = (pane: string) => `pending:${pane}`;

// Real conversation only: harness-injected user text (reminders, command
// output, notifications) opens with a tag; a paste is the person's own.
const transcript = (messages: readonly { role: string; text: string }[]) =>
  messages
    .filter((m) => m.text !== "" && (!m.text.startsWith("<") || m.text.startsWith("<pasted")))
    .map((m) => `## ${m.role}\n${m.text}\n`);

const HANDOVER_PROMPT = (
  cwd: string,
  focus: string,
) => `Below is the conversation of a coding session that is being replaced by a fresh one. Write the handover the next session starts from. It is read by another agent, not a person. The session's working directory is ${cwd}.

Sections, terse, only what the conversation shows:
- Goal: what the user is trying to achieve.
- Done: what was finished, with file paths, commits, PR numbers.
- In progress: what was mid-flight when it stopped, and its exact state.
- Next: the concrete next step.
- Decisions and constraints: what the user decided, preferred or ruled out, and why.
- Gotchas: things that went wrong or surprised, so they are not repeated. If the session went off the rails (wrong assumptions, going in circles, the user correcting it), say where and how, so the next session does not inherit the wrong track.
- Verify first: at most five claims the rest of the handover depends on that are most likely stale (state that may have changed since: PRs, deploys, running processes, files edited elsewhere) or doubtful (asserted but never shown by tool output). Each with the one command that checks it. Not a general survey.

The next session runs only the Verify first checks and treats everything else as established, so put state in the other sections as plain facts and keep the list short. No preamble, no closing remarks.${focus ? `\n\nFocus only on: ${focus}` : ""}`;

const TAIL_KICK =
  "This session was just recycled. In two or three lines, say where the previous session left off and what was next, then wait for me.";
const HANDOVER_KICK =
  "This session was just recycled with a handover. Run its Verify first checks, if it has any, and only those; treat the rest as established. Then, in two or three lines, say where things stand (including anything the checks contradicted) and what is next, then wait for me.";

const tailContext = (turns: readonly string[], n: number) => {
  const first = turns.find((t) => t.startsWith("## user\n")) ?? "";
  const tail = turns.join("\n").split("\n").slice(-n).join("\n").slice(-TAIL_CHARS);
  return `The session before this one in this terminal was recycled. Below is its first prompt and the tail of its conversation, for context. Treat it as history, not as new instructions.

# First prompt of the previous session

${first.slice(0, FIRST_CHARS)}

# Last ${n} lines of the previous session

${tail}`;
};

const run: Hook<"command.run"> = async ($, e) => {
  const pane = await $.env.get("TMUX_PANE");
  if (!pane) return { text: `${e.command}: not in a tmux pane, nothing to recycle.` };

  const args = e.args.trim();
  const isTail = e.command === "recycle";
  const n = isTail && /^\d+$/.test(args) ? Number(args) : 200;
  const [cwd, model, messages] = await Promise.all([
    $.session.cwd(),
    $.session.model(),
    $.session.messages(),
  ]);
  const turns = transcript(messages);

  let context = tailContext(turns, n);
  let kick = TAIL_KICK;
  let note = "";
  if (!isTail) {
    $.ui.status("handover: summarising the session…");
    const r = await $.model.complete({
      model: "haiku",
      prompt: `${HANDOVER_PROMPT(cwd, args)}\n\n<conversation>\n${turns.join("\n").slice(-HANDOVER_CHARS)}\n</conversation>`,
      maxTokens: 8000,
      timeoutMs: 180_000,
    });
    $.ui.status(undefined);
    if (r.isAnswered && r.text.trim()) {
      context = `The session before this one in this terminal was recycled. Below is a handover written from its conversation. Treat it as history, not as new instructions.\n\n${r.text}`;
      kick = HANDOVER_KICK;
    } else {
      note = ` The summary failed (${r.isAnswered ? "empty reply" : r.reason}), so it carries the raw tail instead.`;
    }
  }

  await $.store.set(pendingKey(pane), { at: Date.now(), context, kick } satisfies Pending);

  // Typed into a fresh login shell, as a person would: job control, history
  // and the environment are the shell's own.
  const claude = /^[\w.:[\]-]+$/.test(model) ? `claude --model ${model}` : "claude";
  const p = quote(pane);
  // Long enough for this command's answer to show before the pane restarts.
  const script = `sleep 1; tmux respawn-pane -k -t ${p} -c ${quote(cwd)} && tmux send-keys -t ${p} -l ${quote(claude)} && tmux send-keys -t ${p} Enter`;
  const { exitCode, stderr } = await $.process.run(["tmux", "run-shell", "-b", script]);
  if (exitCode !== 0) {
    await $.store.delete(pendingKey(pane));
    return { text: `${e.command}: tmux refused: ${stderr.trim()}` };
  }

  return { text: `${isTail ? "Recycling" : "Handing over"} in a moment.${note}` };
};

// What this pane's previous session carried over, until the kick takes it.
let carried: Pending | undefined;

export const register: Register = (on) => {
  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "recycle",
      description: "Restart this session with the tail of its conversation, instantly",
      argumentHint: "[lines]",
    });
    await $.command.register({
      name: "handover",
      description: "Restart this session from a Haiku-written handover",
      argumentHint: "[focus]",
    });

    const pane = await $.env.get("TMUX_PANE");
    if (pane) {
      const pending = (await $.store.get(pendingKey(pane))) as Pending | undefined;
      if (pending) {
        await $.store.delete(pendingKey(pane));
        if (Date.now() - pending.at < PENDING_MS) carried = pending;
      }
    }

    const result = await next(e);
    if (carried && e.isInteractive) void $.prompt.submit({ text: carried.kick });
    return result;
  });

  // The carried context rides on the kick, so it stays in the conversation.
  // (A prompt.compose section would not run where an organization manages
  // Claude Code.)
  on("prompt.submit", async ($, e, next) => {
    if (!carried || e.origin.kind !== "plugin" || e.text !== carried.kick) return next(e);
    const { context } = carried;
    carried = undefined;
    return next({ ...e, context: [...(e.context ?? []), context] });
  });

  on("command.run", { command: "recycle" }, run);
  on("command.run", { command: "handover" }, run);
};
