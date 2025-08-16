---
name: memory-compact
description: Consolidate and deduplicate memory files
---

Compact and optimize all memory files.

Execute: `.claude/scripts/memory-commands.sh compact`

This will:
1. Process each agent's memory files
2. Keep only the last 20 entries in work-history.md
3. Remove duplicate entries from lessons and best practices
4. Deduplicate team shared learnings
5. Report reduction in file sizes

Use this periodically to keep memory files lean and efficient.