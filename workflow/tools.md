# Tool Discipline

Prefer the agent's native tools over the shell. Bash is for running programs (builds, tests, git, app binaries) — not for work a dedicated tool already does.

- **Read files** with the Read tool — never `cat`, `sed`, `head`, `tail`, or `less`.
- **Search** with the Grep and Glob tools — not `grep`, `rg`, or `find` in Bash.
- **Edit files** with the Edit/Write tools — not `sed -i`, `echo >`, or here-docs.
- **Invoke skills** with the Skill tool — never run their underlying scripts via Bash.
- **Loading instructions:** reference a standards or instruction file by path for the agent to Read, or `@import` it. Never instruct a shell command (e.g. `cat index.md`) to load it.
