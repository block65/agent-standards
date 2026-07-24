# Narrowing

Narrowing is turning a richer value into a poorer one: an instance into its status, a `Temporal` into a string, a whole object into the one field you sliced off it. Two facts make early narrowing a defect. It is lossy and directional — rich to narrow is always available later, narrow to rich is not — so narrowing before you must only subtracts options from every frame downstream, with no gain that waiting would not also give. And whoever narrows decides what downstream needs; narrow early and one frame makes that decision for every frame after it, without the requirement in front of it.

The rule follows from those two facts:

**Narrowing is consumption. Only the frame that consumes the narrow form is entitled to produce it; everything upstream passes the value at its richest.**

## The test

Follow any value through the code. At each frame ask: does this frame use the narrow form, or does it narrow only to pass the result onward? A frame that transforms-then-passes — stringifies to pass, slices to pass, derives a status to pass — holds a narrowing that belongs to its consumer. Move it down to the frame that uses it.

One question replaces a list of named anti-patterns, and it catches cases nobody has enumerated yet.

## What it catches

- **Create-then-lower.** Building a `Temporal.ZonedDateTime` and calling `.toString()` on it at once, because something several frames down wants a string. Every frame in between now holds a string it cannot compare, offset, or reformat. Carry the `Temporal`; stringify at the frame that writes it out.
- **Read-and-thread.** Reading a derived value off a handle, then threading that value down instead of the handle itself. Each caller repeats the read, and no frame can re-derive it or reach another field once the value is narrowed. Pass the handle; let each consumer read what it needs.
- **A function that takes a projection of its caller.** A function called once, not generic, whose parameters are a slice its single caller had to build first. This is the same narrowing one frame too early: the caller consumed nothing, it pre-narrowed so the callee would not have to hold the whole object. The boundary reads as arbitrary because it is. Give the function the object and move the narrowing inside; the boundary resolves on its own.

## Where narrowing belongs

Narrowing is not the defect — placing it early is. It belongs at genuine exits: the serialization edge, the wire, a cache key, a log line. Those frames consume the narrow form, so that is where the lowering lives. The rule is not "never narrow"; it is narrow at the boundary that needs it, which is almost always further down than the first place it is convenient.
