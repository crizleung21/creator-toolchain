# In-Session Context Policy

- Main implementation stays in the main agent context.
- Subagents are optional and require explicit user authorization.
- Long-running plans must record state in plan artifacts, not hidden memory.
- Do not rely on unstated intent as completion evidence.
