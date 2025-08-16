---
name: memory-help
description: Show all available memory management commands
---

Display comprehensive help for the memory management system.

Show the user:

## Memory Management Commands

### Core Operations
- `/memory-status` - Check system status and agent memories
- `/memory-load <agent> "task"` - Load context for an agent
- `/memory-update <agent> "insights"` - Store new insights
- `/memory-search "term"` - Search all memories for a topic

### Maintenance
- `/memory-clean` - Remove cache files
- `/memory-reset <agent>` - Reset specific agent memory
- `/memory-reset all` - Reset all memories (preserves TRDs)
- `/memory-archive [days]` - Archive old TRDs (default: 30 days)
- `/memory-compact` - Deduplicate and optimize memories

### Knowledge Management
- `/memory-seed <agent> "knowledge"` - Pre-populate agent knowledge
- `/memory-learn "insight"` - Add team-wide learning
- `/memory-project "update"` - Update project context
- `/memory-process-trd <agent> <path>` - Manually process a TRD

### Examples
```bash
/memory-load task-executor "implement login feature"
/memory-search "authentication"
/memory-seed api-specialist "Expert in REST and GraphQL"
/memory-learn "Batch operations improve performance by 30%"
/memory-archive 60
```

Note: All commands work through the memory-manager subagent for intelligent processing.