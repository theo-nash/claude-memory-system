---
name: memory-archive
description: Archive old TRDs to reduce clutter
---

Archive TRDs older than specified days from $ARGUMENTS.

Parse arguments for number of days (default: 30 if not specified).

Execute: `.claude/scripts/memory-commands.sh archive [days]`

This will:
1. Find all TRDs older than the specified number of days
2. Move them to .claude/memory/archive/[agent-name]/
3. Preserve the TRDs for audit trail while reducing active memory clutter
4. Report number of files archived