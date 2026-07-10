# Writing & Documentation Standards

Modular rules for writing. Use the base rules below for everything, then add a specific module if needed.

## No Fluff & High Signal

- **Delete adjectives:** Remove subjective or hyperbolic descriptors. If a sentence works without the adjective, delete it.
- **No unsubstantiated claims:** Avoid bold assertions like "this is rarely done" or "industry standard" unless they are verifiable facts. If there is no evidence, do not state it.

## Write for Humans

- **Structure:** Avoid robotic or legalistic tones. Vary sentence structure.
- **Cohesion:** Combine fragmented thoughts into cohesive paragraphs.
- **No metaphors:** Do not use metaphors, analogies, or figurative language.
  - **Established idioms are fine:** Settled technical terms such as "code smell", "escape hatch", "source of truth", and "user journey" are vocabulary, not figurative language. Novel metaphors coined for the sentence (for example "navigation tax") are not.

## Clarity & Formatting

- **Headings:** Must predict content.
- **Antecedents:** Ensure clear antecedents for "it", "this", "that". Do not use "the [noun]" to reference a specific instance that has not been introduced.

## Prohibited Patterns

- **Filler transitions:** Do not use "However,", "Furthermore,", "Moreover,", "Additionally,", "It's important to note that,", "In today's world,".
- **Excessive em-dashes:** Do not overuse em-dashes to hold a sentence together where a comma, colon, or full stop would serve.
- **Unnecessary lists:** Use prose when a list adds no structural value.
- **Banned vocabulary:** See [Banned Words](banned-words.md) — words banned from all output (prose, comments, commits, chat).

## Modules

Each module file below references this base file as a prerequisite.

- **[Technical Docs](technical.md)**: Objectivity and clarity (No "Your").
- **[Marketing & Copy](marketing.md)**: Persuasion and ownership (Yes "Your").
- **[Decision Records (ADRs)](adr.md)**: Record why, not how; living records kept in sync with the code.
