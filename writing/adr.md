# Decision Records (ADRs)

For reading or writing an Architecture Decision Record. Prerequisite:
[Writing (Base)](base.md).

An ADR records a decision and why it was made. The code and its config are the
source of truth for how.

## Reading an ADR

- **Take the why, not the how:** Act on implementation values from the code,
  never from an ADR.
- **Respect the status:** `Proposed` is not decided; `Deprecated` is no longer
  in force.
- **On drift, decide what drifted:** A deliberate change updates the ADR. A
  regression or unreviewed change gets the code flagged; the record stays.

## Writing an ADR

- **Sections:** Context (what constrained the choice), Decision, Reasoning (why,
  and the trade-off weighed), Consequences.
- **No mechanism:** Leave parameters, config, topology, diagrams and rollout
  steps to the code.
- **Edit in place on change:** Revise the ADR to state the current decision and
  set its status to `Accepted (updated YYYY-MM)`. Git holds the prior version,
  so write no superseding record beside it.

## Status vocabulary

- **`Proposed`**: under consideration.
- **`Accepted`**: in force.
- **`Accepted (updated YYYY-MM)`**: in force, revised in place.
- **`Deprecated`**: no longer applies.
