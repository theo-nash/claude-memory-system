---
name: memory-search
description: Search all memory files for a specific term or subject
---

Use the memory-manager subagent to search for "$ARGUMENTS" across all memory files.

Execute the search by:
1. Calling the memory-manager agent with a search request
2. Have it search through:
   - All agent memory files (work-history, expertise, lessons, current-focus)
   - All TRDs in agent directories
   - Team shared learnings and coordination patterns
   - Project requirements, architecture, and constraints
   - Manager catalogs and priorities

Report findings organized by:
- **Agent Memories**: Which agents have knowledge about this topic
- **TRDs**: Specific task reflections mentioning the search term
- **Team Knowledge**: Shared insights related to the query
- **Project Context**: Requirements or constraints involving this topic
- **Recommendations**: Suggested agents or files to review

Example searches:
- "authentication" - Find all auth-related work and knowledge
- "performance optimization" - Locate performance insights
- "API design" - Find API-related decisions and patterns
- "error handling" - Discover error handling approaches

The memory-manager will provide a comprehensive report of where this knowledge exists in the system.