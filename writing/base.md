# Writing & Documentation Standards

Applies to all writing. Add a module from the list at the end where one fits.

## Content

- **Delete adjectives:** Remove subjective or hyperbolic descriptors. If a
  sentence works without the adjective, delete it.
- **No unsubstantiated claims:** Avoid bold assertions like "this is rarely
  done" or "industry standard" unless they are verifiable facts. Cite the
  evidence with the claim, or cut the claim.
- **No metaphors:** Do not use metaphors, analogies, or figurative language.
  Name the literal mechanism or effect. Settled idioms and technical terms
  ("code smell", "escape hatch", "source of truth") are vocabulary and fine; a
  metaphor coined for the sentence ("navigation tax") is not.
- **Headings predict content.**
- **Antecedents:** Give "it", "this" and "that" a clear antecedent. Introduce
  an entity before referring to it as "the [noun]".

## Form

- **Prose over lists:** Combine fragmented thoughts into paragraphs; use a list
  only where it adds structure.
- **Filler transitions:** Do not use "However,", "Furthermore,", "Moreover,",
  "Additionally,", "It's important to note that,", "In today's world,". Open the
  sentence with its claim, and let sentence order carry the link.
- **Em-dashes:** Join clauses with a comma, colon, or full stop. Keep the
  em-dash for a parenthetical aside.
- **Wrap at 80 columns:** Markdown is read in terminals and diffs. Leave
  frontmatter, code fences and tables alone.

## Examples

- **Show form, not scenarios:** Use bracketed placeholders (`[Component]`,
  `[Reason]`) rather than an invented product, API, or incident. Whatever the
  example contains gets copied along with the form it teaches.
- **Label the two sides in prose:** a `BAD:` or `GOOD:` line above each side's
  own code block, never `❌`/`✅` and never a comment inside the code, which
  becomes a comment in real code.

## Modules

Each names this file as a prerequisite.

- **[Technical Docs](technical.md)**: Objectivity and clarity (No "Your").
- **[Marketing & Copy](marketing.md)**: Persuasion and ownership (Yes "Your").
- **[Decision Records (ADRs)](adr.md)**: Record why, not how; living records
  kept in sync with the code.
