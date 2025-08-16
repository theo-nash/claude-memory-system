---
name: memory-load
description: Load context for a specific agent and task
---

Use the memory-manager subagent to load context for $ARGUMENTS.

Parse the arguments to extract:
1. Agent name (first argument)
2. Task description (remaining arguments)

Then execute:
`./claude-memory load-context [agent-name] "[task-description]"`

This will provide the agent with relevant previous work, lessons learned, and recommendations based on past experience.