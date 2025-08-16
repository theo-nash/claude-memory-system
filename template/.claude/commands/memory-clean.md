---
name: memory-clean
description: Clean up cache files and temporary memory data
---

Clean up memory system cache files.

Execute: `.claude/scripts/memory-commands.sh clean-cache`

This will:
1. Scan the .claude/cache directory for temporary context files
2. Show count of files to be deleted
3. Ask for confirmation before deletion
4. Remove all .md files from the cache directory

Cache files are automatically created during agent operations and should be cleaned periodically.