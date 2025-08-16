---
name: memory-update
description: Update an agent's memories with new insights
---

Use the memory-manager subagent to update memories for $ARGUMENTS.

Parse the arguments to extract:
1. Agent name (first argument)
2. Insights to store (remaining arguments)

Then execute:
`./claude-memory update-memories [agent-name] "[insights]"`

This will process the insights and update the appropriate memory files for the specified agent.