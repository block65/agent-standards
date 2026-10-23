# Tool Discipline

- Invoke a skill with the Skill tool, never its underlying scripts.
- To load a standards file, reference it by path for the agent to Read, or
  `@import` it, never through a shell command such as `cat`.
