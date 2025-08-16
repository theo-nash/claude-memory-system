---
name: memory-process-trd
description: Manually process a Task Reflection Document
---

Process a TRD for a specific agent from $ARGUMENTS.

Parse the arguments to extract:
1. Agent name (first argument)
2. Path to TRD file (second argument)

Execute: `./claude-memory process-trd [agent-name] [trd-path]`

This will:
1. Read the specified TRD file
2. Use memory-manager to analyze its significance
3. Update appropriate memory files based on significance level
4. Spread knowledge to team/project levels if needed

Use this when a TRD wasn't automatically processed or needs reprocessing.