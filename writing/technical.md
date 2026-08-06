# Technical Documentation

**Usage:** Load this file for documentation/support tasks.
**Prerequisite:** Also follow the rules in [Writing (Base)](base.md).

## Objectivity

- **No "Your":** Software has no "you"; "your [Component]" is ambiguous.
  - ❌ "Configure **your** [Component]."
  - ✅ "Configure the **[Location]** [Component]."
- **Subject = component:** In docs for a product, the component acts — never the product's own name.
  - ❌ "[Product] [Action]s the [Component]."
  - ✅ "The [Component] [Action]s."

## Instruction Hierarchy

Follow this order for guides:

1. **Context:** Explain the problem being solved.
2. **Establish:** Define the object or its default state.
3. **Action:** The imperative instruction.

- ❌ "To [Result], click [Action]."
- ✅ "[Component] performs [Function] at the [Layer]. To [Action] it, run the [Command]."

## Language

- **No death metaphors:** No casual death/violence language (e.g., "the connection dies", "if it's dead"). Established technical terms are fine (e.g., "OOM killer", "kill signal", "killed by SIGTERM").
