---
name: memory-project
description: Update project-level context and requirements
---

Update project context with information from $ARGUMENTS.

Execute: `.claude/scripts/memory-commands.sh project "$ARGUMENTS"`

This will:
1. Use memory-manager to analyze the update
2. Determine which project files need updating:
   - requirements.md (functional/non-functional requirements)
   - architecture.md (design decisions, patterns)
   - constraints.md (technical/business limitations)
   - current-state.md (project status, progress)
3. Update the appropriate files
4. Make the information available to all agents