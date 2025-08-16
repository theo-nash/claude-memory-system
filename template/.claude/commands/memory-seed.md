---
name: memory-seed
description: Pre-populate an agent with initial knowledge
---

Seed an agent with initial knowledge from $ARGUMENTS.

Parse the arguments to extract:
1. Agent name (first argument)
2. Initial knowledge (remaining arguments)

Execute: `.claude/scripts/memory-commands.sh seed [agent-name] "[knowledge]"`

This will:
1. Create the agent's memory structure if it doesn't exist
2. Use memory-manager to process and store the seed knowledge
3. Update expertise.md and lessons.md with the provided information
4. Prepare the agent with domain knowledge before first use