---
name: memory-learn
description: Add a team-wide insight or learning
---

Add a team-wide insight from $ARGUMENTS.

Execute: `.claude/scripts/memory-commands.sh learn "$ARGUMENTS"`

This will:
1. Add the insight to .claude/memory/team/shared-learnings.md
2. Tag it with the current date
3. Make it available to all agents
4. Help the entire team benefit from discovered patterns

Use this for insights that apply across multiple agents or domains.