---
name: memory-reset
description: Reset memory for a specific agent or all agents
---

Reset memory files for $ARGUMENTS.

If arguments contain just an agent name:
- Execute: `.claude/scripts/memory-commands.sh reset [agent-name]`
- This preserves TRDs but resets all memory files to initial state

If arguments contain "all":
- Execute: `.claude/scripts/memory-commands.sh reset-all --preserve-trds`
- This resets ALL agent memories while preserving TRDs

Ask for confirmation before executing the reset operation.