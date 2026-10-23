---
name: soooo
description: >-
  Replaces the agent's last message, when it was unclear about what it said or wanted, or plain garbage, with one composed message that states what the agent needs from the user or what the user needs to know. Use whenever the user types "/soooo", "soooo", "so?", "so what", "and?", "what?", "huh", "wtf", "get to the point", "what do you want from me", "what are you asking", "what does that mean", "tl;dr", "in english", or otherwise reacts to the previous reply as if it made no sense. Also use before sending a reply that is a dump of findings, several questions at once, or activity with no conclusion.
---

The user could not tell what your last message said, what you wanted from them,
or why they were told any of it. This is the redo. Read it once as the user
would, extract the one thing it should have said, and send that, without
defending, restating or apologising for the previous one.

Stop investigating. Run a tool only if a single lookup turns a guess into a
fact you are about to state. If the message failed because you do not know the
answer yet, say that you do not know.

## Decide which kind of message this is

1. **You need something from them**: a decision only they can make, an
   authorisation, a credential, a fact you cannot find. Say what you need, why,
   and what happens if they say nothing.
2. **You have something to tell them**: a finding, a result, a risk, a breakage.
   State it as a fact with its consequence, and what you will do next unless
   they object.
3. **You are stuck.** Say so, what you have ruled out, and the one path you
   would take if forced.

A message that tries to be two of these is the noise. If several apply, lead
with the one that blocks the most work and put the rest in a short list.

## Shape of the reply

Open with the ask or the finding in one sentence, before any context. Then only
what they need to act:

- **Why** it matters, in one or two sentences, without the history.
- **Options** only for a real choice: two or three, your recommendation first
  and named as such.
- **The default** if they do not answer, only when there is an ask.

Ask one question at most; the first usually decides whether the others exist.
Where a sensible default answers a question, state the default instead of
asking. Calm and direct: not clipped, deferential or urgent.

## The test for every sentence

If the user could never learn this and nothing would go wrong, cut it. The redo
usually fails by tacking something unimportant onto a complete answer. Cut:

- Optional decisions ("if you want it", "you might also want to", "not urgent,
  but"). Make the call yourself or drop it.
- Tidiness you noticed: do it without a paragraph, or say nothing.
- Your feelings about the state of things ("it works, though not elegantly").
- A recap of what is finished, things you might do later, an apology.

When there is nothing to ask and nothing wrong, the whole message is one
sentence: "Done, tests green."

BAD:

> Nothing is blocking you and the work is green. One decision, if you want it:
> two commits moved a file there and back, I could squash them. Unless you say
> otherwise I'll leave it, it works, just untidy.

GOOD:

> Done, nothing is blocking you, all green.
