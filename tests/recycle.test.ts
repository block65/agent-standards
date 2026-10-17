import type { ModelCompleteResult, On, SessionMessage } from "claude-code";
import { expect, test } from "claude-code/testing";

// Typed at the prompt, in tmux's main-screen layout
const typed = {
  origin: { kind: "composer" },
  presentation: { isFullscreen: false, columns: 80 },
} as const;

const conversation: SessionMessage[] = [
  { role: "user", text: "first ask", toolUses: [] },
  { role: "user", text: "<system-reminder>noise</system-reminder>", toolUses: [] },
  { role: "assistant", text: "did it", toolUses: [] },
];

const usage = {
  input_tokens: 1,
  output_tokens: 1,
  cache_read_input_tokens: 0,
  cache_creation_input_tokens: 0,
};
const handover: ModelCompleteResult = { isAnswered: true, text: "THE HANDOVER", usage };

function inTmux(on: On, summary: ModelCompleteResult) {
  const world = {
    runs: new Array<readonly string[]>(),
    store: new Map<string, unknown>(),
    asks: new Array<string>(),
  };
  on("env.get", async () => ({ value: "%42" }));
  on("clock.now", async () => ({ value: 1000 }));
  on("session.cwd", async () => ({ value: "/work/it's here" }));
  on("session.model", async () => ({ value: "claude-opus-5-5" }));
  on("session.messages", async () => ({ value: conversation }));
  on("model.complete", async ($, e) => {
    world.asks.push(e.prompt);

    return { value: summary };
  });
  on("store.set", async ($, e) => {
    world.store.set(e.key, e.value);

    return { value: undefined };
  });
  on("store.delete", async ($, e) => {
    world.store.delete(e.key);

    return { value: undefined };
  });
  on("process.run", async ($, e) => {
    world.runs.push(e.argv);

    return {
      value: {
        exitCode: 0,
        stdout: "",
        stderr: "",
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    };
  });

  return world;
}

const respawn = `sleep 1; tmux respawn-pane -k -t '%42' -c '/work/it'\\''s here' && tmux send-keys -t '%42' -l 'claude --model claude-opus-5-5' && tmux send-keys -t '%42' Enter`;

test("/handover stores a Haiku handover for the pane and types claude into a fresh shell", async ($, on) => {
  const world = inTmux(on, handover);

  const out = await $.command.run({ ...typed, command: "handover", args: " the CSP work " });

  expect(out.text).toBe("Handing over in a moment.");
  expect(world.asks[0]).toContain("The session's working directory is /work/it's here.");
  expect(world.asks[0]).toContain("Focus only on: the CSP work");
  expect(world.asks[0]).toContain("## user\nfirst ask");
  expect(world.asks[0]).not.toContain("noise");
  expect(world.store.get("pending:%42")).toMatchObject({
    at: 1000,
    context: expect.stringContaining("THE HANDOVER"),
    kick: expect.stringContaining("Verify first"),
  });
  expect(world.runs).toEqual([["tmux", "run-shell", "-b", respawn]]);
});

test("/recycle sends the raw tail with no model call", async ($, on) => {
  const world = inTmux(on, handover);

  await $.command.run({ ...typed, command: "recycle", args: "300" });

  expect(world.asks).toEqual([]);
  expect(world.store.get("pending:%42")).toMatchObject({
    context: expect.stringMatching(
      /# Last 300 lines of the previous session[\s\S]*## assistant\ndid it/,
    ),
  });
  expect(world.runs).toEqual([["tmux", "run-shell", "-b", respawn]]);
});

test("a failed summary falls back to the raw tail and says so", async ($, on) => {
  const world = inTmux(on, { isAnswered: false, reason: "empty-reply", usage });

  const out = await $.command.run({ ...typed, command: "handover", args: "" });

  expect(out.text).toContain("summary failed (empty-reply)");
  expect(world.store.get("pending:%42")).toMatchObject({
    context: expect.stringContaining("# Last 200 lines"),
  });
});

test("outside tmux it does nothing", async ($, on) => {
  on("env.get", async () => ({ value: undefined }));
  on("process.run", async () => {
    throw new Error("must not run");
  });

  const out = await $.command.run({ ...typed, command: "recycle", args: "" });

  expect(out.text).toContain("not in a tmux pane");
});
