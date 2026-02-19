# Module: Technical Documentation

**Usage:** Load AFTER `workflow/writing.md` for Documentation/Support.
**Purpose:** Enforces objectivity, precision, and instruction clarity.

## 1. Objectivity Rules

### The "No 'Your'" Mandate
- **Rule:** The system functions objectively. Software does not know "you."
- **Reasoning:** In complex topologies, "your node" is ambiguous.
    - ❌ "Configure **your** firewall."
    - ✅ "Configure the **edge** firewall."

### System Behavior
- **Subject = Component:** Do not use the product name as the subject of a functional description.
    - ❌ "Wallhack creates a tunnel."
    - ✅ "A tunnel is initialized."

## 2. Instruction Hierarchy
Follow this strict order for guides:
1.  **Context (Why):** Explain the problem.
2.  **Establish (What):** Define the object/default.
3.  **Action (How):** The imperative instruction.

* ❌ "To route traffic, click start."
* ✅ "A TUN interface routes traffic at the network layer. To initialize it, run the start command."
