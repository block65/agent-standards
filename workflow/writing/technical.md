# Module: Technical Documentation

**Usage:** Load AFTER `workflow/writing.md` for Documentation/Support.
**Purpose:** Enforces objectivity, precision, and instruction clarity.

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
1.  **Context (Why):** Explain the problem.
2.  **Establish (What):** Define the object/default.
3.  **Action (How):** The imperative instruction.

* ❌ "To [Result], click [Action]."
* ✅ "[Component] performs [Function] at the [Layer]. To [Action] it, run the [Command]."
