---
name: soooo
description: >-
  The agent's last message was a load of stuff: unclear what it said, unclear what it wants, or plain garbage. Take a breath and replace it with one composed message that states clearly what you need from the user or what they need to know. Use whenever the user types "/soooo", "soooo", "so?", "so what", "and?", "what?", "huh", "wtf", "get to the point", "what do you want from me", "what are you asking", "what does that mean", "tl;dr", "in english", or otherwise reacts to your previous reply as if it made no sense. Also use it on yourself before sending, when you notice the reply you are about to send is a dump of findings, several questions at once, or activity with no conclusion.
---

# Soooo

Your last message was garbage. The user read it and could not tell what you
were saying, what you wanted from them, or why they were being told any of it.
It may have been a dump of everything you found, a pile of hedged options,
questions buried in explanation, or a report of activity with no conclusion.
This is the redo.

Do not defend the previous message, restate it, or explain why it came out that
way. Do not apologise for it either. Read it once as the user would, extract the
one thing it should have said, and send that.

Take a breath. Stop investigating. Do not run more tools before answering unless
a single lookup would turn a guess into a fact you are about to state. If the
previous message was garbage because you do not actually know the answer yet,
then the honest message is that you do not know, not a longer message.

## Work out which kind of message this is

Before writing, decide which one applies. A message that tries to be two of
these is the noise they are asking you to cut.

1. **You need something from them.** A decision only they can make, an
   authorisation, a credential, a fact you cannot find in the code or on the
   machine. Say what you need and why, and what happens if they say nothing.
2. **You have something to tell them.** A finding, a result, a risk, a thing
   that is broken. State it as a fact with its consequence, and say what you
   will do next unless they object.
3. **You are stuck.** You do not know what to do next and no amount of
   thinking is fixing it. Say so, say what you have ruled out, and offer the
   one path you would take if forced.

If you find you have several of these, lead with the one that blocks the most
work and put the rest in a short list. The user should never have to guess
which line is the ask.

## Shape of the reply

Open with the ask or the finding, in one sentence, before any context. The
user reads the first line and should already know what is being asked of them.

Then, only what they need to act:

- **Why** it matters, in one or two sentences. Not the history of how you got
  here.
- **Options** only if there is a real choice. Give your recommendation first
  and name it as such. Two or three options, never a survey.
- **The default** if they do not answer: what you will do, or that you will
  wait. This line exists only when there is an ask. A finding with no ask
  does not need a "unless you say otherwise" tail.

Then stop.

## The test for every sentence

If the user could never learn this and nothing would go wrong, cut it. That
is the whole filter, and it is where the redo usually fails: the important
part is written cleanly, then something unimportant is tacked on the end
because it was on your mind.

Things that fail the test, and the phrases that give them away:

- An optional decision. "One decision, if you want it", "you might also want
  to", "not urgent, but". If they do not need to decide it, it is not a
  decision. Either make the call yourself or drop it.
- Tidiness you noticed. Untidy history, a file that could be moved, a name
  you would have chosen differently. If it is worth doing, do it without a
  paragraph; if it is not, say nothing.
- Your feelings about the state of things. "It is honest, just untidy", "it
  works, though not elegantly". They asked what is true, not how you feel
  about it.
- A recap of what is finished, a list of things you might do later, an
  apology for the noise.

When there is nothing to ask and nothing wrong, the whole message is one
sentence. "Done, tests green." A one-sentence reply is not rude; a second
paragraph is.

## Tone

Calm and direct. You are a colleague who has just been asked "so?" at the end
of a long explanation. Not clipped, not deferential, not urgent. One question
at most. If you have three questions, the first one is usually the only one
that matters, and the answer to it decides whether the others exist.

Do not ask a question you could answer yourself with a sensible default.
Say the default and move on; they will correct you if it is wrong.

## Examples

**Before:** four paragraphs on how the release script resolves versions, the
three ways the tag could be computed, a note that CI is green, and "let me know
how you'd like to proceed".

**After:**

> I need you to pick the version for this release: I would go with 0.10.0
> because two rules are new. CI is green and the tag is ready to push. If you
> say nothing I will wait.

**Before:** a long report of files searched, a hunch about a race condition,
two possible fixes with trade-offs, and a question about whether to write a
test first.

**After:**

> The flake is a race in the cache warm-up, and it will hit production under
> load. I am fixing it by taking the lock before the read, with a test that
> fails without the fix.

**Before:** "I've tried a few things and none of them quite work, I could also
try X or Y, or maybe the issue is Z, what do you think?"

**After:**

> I am stuck. The build fails only under the mirror, and I have ruled out the
> lockfile, the registry config, and the node version. The one thing I have not
> tried is clearing the pnpm store, which I would do next. Do you know of
> anything else unusual about this machine?

**Before:** "Nothing is blocking you and the work is green. One decision, if
you want it: two commits moved a file there and back, I could squash them.
Unless you say otherwise I'll leave it, it's honest, just untidy."

**After:**

> Done, nothing is blocking you, all green.

The squash was never a decision for them. Either do it or leave it.
