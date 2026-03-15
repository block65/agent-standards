# Module: Technical Documentation

**Usage:** Load this file for Documentation/Support tasks.
**Prerequisite:** Also follow the base rules in [base.md](base.md).

## 1. Objectivity Rules

### The "No 'Your'" Mandate
- **Rule:** The system functions objectively. Software does not know "you."
- **Reasoning:** In complex environments, "your [Component]" is ambiguous.
    - ❌ "Configure **your** [Component]."
    - ✅ "Configure the **[Location]** [Component]."

### System Behavior
- **Subject = Component:** Do not use the product name as the subject of a functional description.
    - ❌ "[Product] [Action]s the [Component]."
    - ✅ "A [Component] is [Action]ed."

## 2. Instruction Hierarchy
Follow this strict order for guides:
1.  **Context:** Explain the problem being solved.
2.  **Establish:** Define the object or its default state.
3.  **Action:** The imperative instruction.

* ❌ "To [Result], click [Action]."
* ✅ "[Component] performs [Function] at the [Layer]. To [Action] it, run the [Command]."

## 3. Language
- **Death metaphors:** No casual death/violence language (e.g., "the connection dies", "if it's dead"). Established technical terms are fine (e.g., "OOM killer", "kill signal", "killed by SIGTERM").
