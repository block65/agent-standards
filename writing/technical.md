# Technical Documentation

For documentation and support writing. Prerequisite:
[Writing (Base)](base.md).

## Objectivity

- **No "Your":** Name the component and its location; "your [Component]" is
  ambiguous.
  - BAD: "Configure **your** [Component]."
  - GOOD: "Configure the **[Location]** [Component]."
- **Subject = component:** In docs for a product, the component acts, never the
  product's own name.
  - BAD: "[Product] [Action]s the [Component]."
  - GOOD: "The [Component] [Action]s."

## Instruction order

In a guide, state the problem, then the object or its default state, then the
imperative instruction.

- BAD: "To [Result], click [Action]."
- GOOD: "[Component] performs [Function] at the [Layer]. To [Action] it, run the
  [Command]."

## Language

- **No death metaphors:** State what happened: "the connection closed", "the
  process exited", not "the connection dies". Established terms ("OOM killer",
  "kill signal", "killed by SIGTERM") are fine.
