# Tool Discipline

- Invoke a skill with the Skill tool, never its underlying scripts.
- A subagent loads only what its brief points at. A brief for code work names
  `agent-standards/index.md` and the modules the task needs.
- To load a standards file, reference it by path for the agent to Read, or
  `@import` it, never through a shell command such as `cat`.
