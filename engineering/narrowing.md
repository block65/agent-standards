# Narrowing

Narrowing turns a richer value into a poorer one: an instance into its status, a
`Temporal` into a string, an object into one field. It is lossy and one-way, and
the frame that narrows decides for every frame after it what they can have.

**Only the frame that consumes the narrow form produces it; everything upstream
passes the value at its richest.**

## The test

At each frame a value passes through, ask whether the frame uses the narrow form
or narrows only to pass the result on. A frame that stringifies, slices or
derives a status to pass it on holds a narrowing that belongs to its consumer.
Move it down to that consumer.

## What it catches

- **Create-then-lower.** Building a `Temporal.ZonedDateTime` and calling
  `.toString()` at once because a frame further down takes a string. Every frame
  between holds a string it cannot compare, offset or reformat. Carry the
  `Temporal`; stringify where it is written out.
- **Read-and-thread.** Reading a derived value off a handle and threading that
  value down. No frame below can reach another field. Pass the handle; let each
  consumer read what it needs.

## Where narrowing belongs

At the exits that consume the narrow form: the serialization edge, the wire, a
cache key, a log line. That is usually further down than the first convenient
place.

A host or vendor boundary is the one entry that narrows. The adapter converts
the host's objects (a request event, an execution context, an SDK client) into
the core's own types, so every host passes the core the same shape and the core
names no platform type.
