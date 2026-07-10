# Decision Records (ADRs)

**Usage:** Load when reading or writing an Architecture Decision Record.
**Prerequisite:** Also follow the rules in [Writing (Base)](base.md).

An ADR records a decision: the choice made and why it was made. It is not a
spec, a how-to, or current-state documentation of the system.

An ADR is a living record. Keep it in sync with the current code and the
current decision. When a decision changes, edit the ADR to reflect the new
choice and mark it `Updated`. Git holds the prior versions, so there is no
need to accumulate superseded records in the tree.

## Reading an ADR

- **It tells you _why_, not _how_.** The code and its config are the source of
  truth for how. Never lift an implementation value out of an ADR and act on
  it.
- **Status is meaningful, not decorative.** `Proposed` is not decided;
  `Deprecated` is no longer in force.
- **On drift, the code wins.** The fix is to update the ADR, not the code.

## Writing an ADR

- **Record the choice and why it was made.** Cover the Context (what
  constrained the choice), the Decision (the choice), the Reasoning (why, and
  the trade-off weighed), and the Consequences.
- **Nothing about mechanism.** No parameters, config, topology, diagrams, or
  rollout steps. Those are not decisions; they live in the code.
- **On change, edit in place.** Revise the ADR to state the current decision
  and mark it `Updated`. Do not leave a stale record beside a new one.

## Status vocabulary

- **`Proposed`** — under consideration, not yet decided.
- **`Accepted`** — the decision in force.
- **`Deprecated`** — the decision no longer applies.
- **`Updated`** — a marker on an `Accepted` record whose decision has since
  changed and been revised in place.
