# Tool Discipline

Use the agent's native tools for files, and Bash for running programs (builds,
tests, git, app binaries). This overrides a harness that permits shell file
work.

- Read with the Read tool, not `cat`, `sed`, `head` or `tail`; those serve only
  as filters on command output.
- Search with the Grep and Glob tools, not `grep`, `rg` or `find`.
- Edit with the Edit and Write tools, not `sed -i`, `echo >` or heredocs.
- Invoke a skill with the Skill tool, never its underlying scripts.
- To load a standards file, reference it by path for the agent to Read, or
  `@import` it, never through a shell command such as `cat`.
