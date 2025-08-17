#!/usr/bin/env python3
"""
SessionStart Hook: Initialize Complete Agent System

This comprehensive initialization hook prepares all agents for effective collaboration by:

1. **Protocol Setup**:
   - Adds TRD (Task Reflection Document) protocol for knowledge capture
   - Adds Inter-Agent Messaging protocol for direct communication
   - Personalizes both protocols with each agent's actual name from frontmatter

2. **Tool Configuration**:
   - Ensures all agents have access to MCP messaging tools
   - Adds tools to restricted lists when needed
   - Handles special cases (e.g., memory-manager gets tools but not protocols)

3. **Memory Scaffolding**:
   - Creates complete memory directory structure for all agents
   - Initializes placeholder memory files (work-history, current-focus, expertise, lessons)
   - Sets up team, project, and manager directories

4. **Agent Identity**:
   - Parses agent names from YAML frontmatter (not filename)
   - Ensures consistent naming across all systems
   - Falls back to filename if no frontmatter exists

Runs silently at SessionStart to ensure all agents are properly configured for both
memory retention and inter-agent communication.
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

def get_trd_protocol(agent_name):
    """Generate the TRD protocol section for an agent"""
    return f"""

## Task Reflection Document (TRD) Protocol

**MANDATORY**: Before completing any task, you MUST create a Task Reflection Document.

### When to Create
- After completing your main task objectives
- Before reporting final completion to the user
- Even for simple tasks (mark as "Routine" significance)

### TRD Location
Save to: `.claude/memory/agents/{agent_name}/trds/trd-YYYY-MM-DD-HHMM-[session_id].md`

The filename will be provided in your task prompt. If not provided, use the format above with current timestamp.

### TRD Format
```markdown
# Task Reflection Document
Date: [ISO timestamp]
Agent: {agent_name}
Task: [One-line summary of what you were asked to do]

## Significance Level
[Choose ONE: Routine | Notable | Significant]
- Routine: Standard work, no major insights, familiar patterns
- Notable: Useful learnings, coordination needs, interesting discoveries
- Significant: Major insights, architecture changes, breakthrough solutions

## What I Did
- [Bullet points of specific actions taken]
- [Tools used and why]
- [Files created/modified]

## Key Insights
- [Technical discoveries, patterns, optimizations]
- [What worked well, what didn't]
- [Surprising findings or confirmations]

## Messages Sent
- [Messages sent to other agents via create_message(), or "None"]
- [Format: "To [agent]: [brief summary of message]"]
- [Note: Use messaging tools for direct coordination, not handoffs]

## Issues for Follow-up
- [Problems needing attention, or "None"]
- [Blockers, errors, incomplete items]
- [Questions that arose during work]

## For Team Knowledge
- [Insights applicable to other team members, or "None"]
- [Reusable patterns, shared utilities]
- [Coordination improvements]

## For Project Knowledge
- [New requirements/constraints discovered, or "None"]
- [Architecture decisions, global impacts]
- [Technical debt or improvements needed]

## What I Learned
- [Areas of improvement to make your work more efficient next time]
- [Patterns or processes to improve your work]
- [Errors you made to avoid in the future]
```

### Significance Guidelines
- **Routine**: ~70% of tasks. Standard implementation, using known patterns
- **Notable**: ~25% of tasks. Found something useful, sent important messages, or hit interesting issues
- **Significant**: ~5% of tasks. Major discoveries, architecture changes, or breakthrough solutions

This TRD is critical for team learning and knowledge sharing. Creating it helps future tasks build on your discoveries and avoid repeated mistakes.
"""

def get_messaging_protocol(agent_name):
    """Generate the messaging protocol section for an agent"""
    return f"""

## Inter-Agent Messaging Protocol

**IMPORTANT**: You have MCP tools for direct agent-to-agent communication.

### At Session Start
1. **Check messages**: Always check for messages from other agents first
   ```
   read_messages(agent_name="{agent_name}")
   ```
2. **List available agents**: See who you can communicate with
   ```
   list_agents()
   ```

### During Your Work
When you discover information relevant to another agent:
```
create_message(
    from_agent="{agent_name}",
    to_agent="target-agent-name",
    message="Specific information they need",
    priority="high"  # or "medium", "low"
)
```

### Message Guidelines
- **High priority**: Blocking issues, critical information
- **Medium priority**: Coordination needs, useful updates
- **Low priority**: FYI, non-urgent discoveries

### What to Share via Messages
- Specific technical details (e.g., "Permission system uses bitmap: 0x0001=READ")
- Completed work ready for next agent (e.g., "API endpoints complete at /api/v2/")
- Blockers or issues (e.g., "Database schema missing user_roles table")
- Important discoveries (e.g., "Found existing auth system in /lib/auth/")

### Identity Consistency
- Always use "{agent_name}" as your agent name in all messaging operations
- This ensures messages are properly routed to and from you

### Before Completing Tasks
If you discovered information useful to specific agents but didn't send it during work:
- Review your findings
- Send relevant messages to appropriate agents
- Use `clear_messages(agent_name="{agent_name}")` if inbox is cluttered
"""

def has_trd_protocol(content):
    """Check if file already has TRD protocol"""
    indicators = [
        "Task Reflection Document",
        "TRD Protocol",
        "## Task Reflection Document (TRD)",
        "MANDATORY**: Before completing any task, you MUST create"
    ]
    return any(indicator in content for indicator in indicators)

def has_messaging_protocol(content):
    """Check if file already has messaging protocol"""
    indicators = [
        "Inter-Agent Messaging Protocol",
        "read_messages(agent_name=",
        "create_message(from_agent=",
        "## Inter-Agent Messaging"
    ]
    return any(indicator in content for indicator in indicators)

def parse_agent_frontmatter(content: str) -> Optional[Dict[str, str]]:
    """Parse agent file to extract name and other fields from frontmatter"""
    if not content.startswith('---'):
        return None
        
    # Find the end of frontmatter
    lines = content.split('\n')
    end_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break
            
    if end_index == -1:
        return None
        
    # Parse the frontmatter
    name = None
    description = None
    tools = None
    
    for i in range(1, end_index):
        line = lines[i]
        if line.startswith('name:'):
            name = line.split(':', 1)[1].strip()
        elif line.startswith('description:'):
            description = line.split(':', 1)[1].strip()
        elif line.startswith('tools:'):
            tools = line.split(':', 1)[1].strip()
            
    if name:
        return {
            'name': name,
            'description': description or '',
            'tools': tools or ''
        }
    return None

def ensure_mcp_tools_access(content, agent_name):
    """Ensure agent has access to MCP messaging tools"""
    # MCP messaging tools that agents need
    mcp_tools = [
        'mcp__agent-messaging__create_message',
        'mcp__agent-messaging__read_messages',
        'mcp__agent-messaging__clear_messages',
        'mcp__agent-messaging__list_agents'
    ]
    
    # Parse frontmatter to check tools configuration
    if not content.startswith('---'):
        return content, False
    
    # Find the end of frontmatter
    lines = content.split('\n')
    end_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break
    
    if end_index == -1:
        return content, False
    
    # Check if tools line exists in frontmatter
    tools_line_index = -1
    tools_value = None
    for i in range(1, end_index):
        if lines[i].startswith('tools:'):
            tools_line_index = i
            tools_value = lines[i].split(':', 1)[1].strip()
            break
    
    # If no tools specified or "All" specified, agent has access to all tools
    if tools_line_index == -1 or tools_value in ['All', 'all', '"All"', "'All'"]:
        # Agent already has access to all tools (including MCP)
        return content, False
    
    # Parse existing tools
    existing_tools = [t.strip() for t in tools_value.split(',')]
    
    # Check if MCP tools are already present
    has_all_mcp = all(tool in existing_tools for tool in mcp_tools)
    
    if has_all_mcp:
        return content, False
    
    # Add missing MCP tools
    missing_tools = [tool for tool in mcp_tools if tool not in existing_tools]
    all_tools = existing_tools + missing_tools
    
    # Format the new tools line (break into multiple lines if too long)
    tools_joined = ', '.join(all_tools)
    if len(tools_joined) > 150:  # Increased threshold
        # Multi-line format - using proper YAML list syntax
        tools_str = 'tools:\n'
        for tool in all_tools:
            tools_str += f'  - {tool}\n'
        tools_str = tools_str.rstrip('\n')  # Remove last newline
    else:
        # Single line format
        tools_str = 'tools: ' + tools_joined
    
    # Replace the tools line
    lines[tools_line_index] = tools_str
    
    # Reconstruct content
    new_content = '\n'.join(lines)
    return new_content, True

def add_protocols_to_agent(agent_path, filename_based_name):
    """Add TRD and messaging protocols to an agent definition file, and ensure MCP tools access"""
    
    # Read current content
    with open(agent_path, 'r') as f:
        content = f.read()
    
    # Parse frontmatter to get actual agent name
    frontmatter = parse_agent_frontmatter(content)
    if frontmatter and frontmatter['name']:
        agent_name = frontmatter['name']
    else:
        # Fallback to filename if no frontmatter or name field
        agent_name = filename_based_name
        print(f"  ⚠️  {filename_based_name}: No name in frontmatter, using filename")
    
    # Track what was added/modified
    added_trd = False
    added_messaging = False
    added_tools = False
    
    # First ensure MCP tools access (modifies frontmatter)
    content, added_tools = ensure_mcp_tools_access(content, agent_name)
    
    # Check and add TRD protocol if missing
    if not has_trd_protocol(content):
        trd_section = get_trd_protocol(agent_name)
        content = content.rstrip() + trd_section
        added_trd = True
    
    # Check and add messaging protocol if missing
    if not has_messaging_protocol(content):
        messaging_section = get_messaging_protocol(agent_name)
        content = content.rstrip() + messaging_section
        added_messaging = True
    
    # Write back if anything was added/modified
    if added_trd or added_messaging or added_tools:
        with open(agent_path, 'w') as f:
            f.write(content)
        
        # Report what was added
        updates = []
        if added_trd:
            updates.append("TRD protocol")
        if added_messaging:
            updates.append("messaging protocol")
        if added_tools:
            updates.append("MCP tools")
        
        print(f"  ✅ {agent_name}: Added {', '.join(updates)}")
        return True
    else:
        print(f"  ⏭️  {agent_name}: Already has all protocols and tools")
        return False

def ensure_manager_scaffolding(claude_dir, is_hook=False):
    """Create manager directory with core files"""
    manager_dir = claude_dir / "memory" / "manager"
    manager_dir.mkdir(parents=True, exist_ok=True)
    
    manager_files = {
        "team-roster.md": """# Team Roster

## Active Agents
*To be populated as agents are initialized*

<!-- Format:
- **agent-name**: Role description
-->
""",
        "project-overview.md": """# Project Overview

## Description
*Project description to be added*

## Goals
*Project goals to be defined*

## Current Status
*Status to be updated*
""",
        "current-priorities.md": """# Current Priorities

## High Priority
*No high priority items*

## Medium Priority
*No medium priority items*

## Low Priority
*No low priority items*
""",
        "document-catalog.md": """# Document Catalog

## Agent TRDs
*No TRDs documented yet*

## Team Knowledge
*No team documents yet*

## Project Context
*No project documents yet*
"""
    }
    
    created = 0
    for filename, content in manager_files.items():
        file_path = manager_dir / filename
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            created += 1
    
    return created > 0

def ensure_team_scaffolding(claude_dir, is_hook=False):
    """Create team directory with shared files"""
    team_dir = claude_dir / "memory" / "team"
    team_dir.mkdir(parents=True, exist_ok=True)
    
    team_files = {
        "shared-learnings.md": """# Shared Learnings

## Cross-Agent Insights
*No shared learnings yet*
""",
        "coordination-patterns.md": """# Coordination Patterns

## Established Workflows
*No patterns documented yet*

## Agent Dependencies
<!-- Track which agents typically work together -->
*No patterns established yet*
"""
    }
    
    created = 0
    for filename, content in team_files.items():
        file_path = team_dir / filename
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            created += 1
    
    return created > 0

def ensure_project_scaffolding(claude_dir, is_hook=False):
    """Create project directory with context files"""
    project_dir = claude_dir / "memory" / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    project_files = {
        "requirements.md": """# Project Requirements

## Functional Requirements
*To be defined*

## Non-Functional Requirements
*To be defined*
""",
        "architecture.md": """# Architecture Decisions

## Design Patterns
*No patterns documented*

## Technology Stack
*To be defined*
""",
        "constraints.md": """# Project Constraints

## Technical Constraints
*No constraints documented*

## Business Constraints
*No constraints documented*
""",
        "current-state.md": """# Current Project State

## Completed Features
*None yet*

## In Progress
*None yet*

## Planned
*To be defined*
"""
    }
    
    created = 0
    for filename, content in project_files.items():
        file_path = project_dir / filename
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            created += 1
    
    return created > 0

def ensure_memory_scaffolding(agent_name, claude_dir, is_hook=False):
    """Create complete memory directory structure and placeholder files for an agent"""
    memory_base = claude_dir / "memory" / "agents" / agent_name
    
    # Create directory structure
    dirs_to_create = [
        memory_base,
        memory_base / "trds"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Define simplified 4-file structure with placeholder content
    memory_files = {
        "work-history.md": f"""# {agent_name}: Work History

## Recent Completed Work
*No completed tasks yet*

<!-- Format: 
- **YYYY-MM-DD**: Brief task description - outcome/deliverable (TRD: filename)
-->
""",
        "current-focus.md": f"""# {agent_name}: Current Focus

## Active Work
*No active work*

## Ready for Others
*No work ready for other agents*
<!-- Format: Work description → Ready for agent-name -->

## Waiting On
*Not waiting on any dependencies*
<!-- Format: Work description ← Waiting on agent-name -->

## Next Priorities
*To be determined*
""",
        "expertise.md": f"""# {agent_name}: Expertise

## Domain Knowledge
*No domain expertise documented yet*

## Technical Skills
*No technical skills recorded yet*

## Specialized Areas
*No specializations defined yet*
""",
        "lessons.md": f"""# {agent_name}: Lessons

## What Works Well
*No successful patterns documented yet*

## What to Avoid
*No pitfalls documented yet*

## Key Insights
*No insights recorded yet*

## Best Practices
*No best practices established yet*
"""
    }
    
    # Create only missing files
    created_files = 0
    for filename, content in memory_files.items():
        file_path = memory_base / filename
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            created_files += 1
            if not is_hook:
                print(f"  📄 Created memory file: {filename}")
    
    # Create TRDs directory
    trd_dir = memory_base / "trds"
    if not trd_dir.exists():
        trd_dir.mkdir(parents=True, exist_ok=True)
        if not is_hook:
            print(f"  📁 Created TRD directory")
    
    return created_files > 0 or not trd_dir.exists()

def main():
    # Check if running as SessionStart hook
    is_hook = False
    try:
        # Try to read stdin for hook data (will be present if called as hook)
        if not sys.stdin.isatty():
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                hook_data = json.load(sys.stdin)
                is_hook = hook_data.get('hook_event_name') == 'SessionStart'
    except:
        pass
    
    # Find .claude/agents directory
    # Script is in .claude/hooks/, so go up one level to .claude/
    script_dir = Path(__file__).parent  # .claude/hooks/
    claude_dir = script_dir.parent      # .claude/
    agents_dir = claude_dir / "agents"
    
    if not agents_dir.exists():
        if not is_hook:
            print(f"❌ Agents directory not found at {agents_dir}")
        sys.exit(0)  # Exit gracefully for hooks
    
    # Only print headers if not running as hook
    if not is_hook:
        print("🔧 Initializing Agent Memory System")
        print("=" * 50)
    
    # Ensure all scaffolding directories first
    ensure_manager_scaffolding(claude_dir, is_hook)
    ensure_team_scaffolding(claude_dir, is_hook)
    ensure_project_scaffolding(claude_dir, is_hook)
    
    # Create cache directory
    cache_dir = claude_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all .md files in agents directory
    agent_files = list(agents_dir.glob("*.md"))
    
    if not agent_files:
        if not is_hook:
            print("❌ No agent definition files found")
        sys.exit(0)
    
    updated_count = 0
    skipped_count = 0
    
    for agent_file in agent_files:
        filename_based_name = agent_file.stem
        
        # Parse the file to get the actual agent name
        with open(agent_file, 'r') as f:
            file_content = f.read()
        
        frontmatter = parse_agent_frontmatter(file_content)
        if frontmatter and frontmatter['name']:
            actual_agent_name = frontmatter['name']
        else:
            actual_agent_name = filename_based_name
        
        # Don't skip memory-manager for tools check, but skip protocols
        if actual_agent_name == "memory-manager":
            # Only check/add MCP tools for memory-manager
            content = file_content  # Already read above
            
            content, added_tools = ensure_mcp_tools_access(content, actual_agent_name)
            
            if added_tools:
                with open(agent_file, 'w') as f:
                    f.write(content)
                if not is_hook:
                    print(f"  ✅ {actual_agent_name}: Added MCP tools (protocols skipped)")
                updated_count += 1
            else:
                if not is_hook:
                    print(f"  ⏭️  {actual_agent_name}: Has MCP tools (protocols skipped)")
                skipped_count += 1
            
            # Still ensure memory scaffolding
            ensure_memory_scaffolding(actual_agent_name, claude_dir, is_hook)
            continue
        
        # Add protocols (suppress output if running as hook)
        original_print = print if not is_hook else lambda *args, **kwargs: None
        
        # Temporarily replace print for the function call
        _print = print
        if is_hook:
            import builtins
            builtins.print = lambda *args, **kwargs: None
        
        if add_protocols_to_agent(agent_file, filename_based_name):
            updated_count += 1
        else:
            skipped_count += 1
        
        # Always ensure memory scaffolding for all agents (except memory-manager)
        # Use the actual agent name for memory scaffolding
        ensure_memory_scaffolding(actual_agent_name, claude_dir, is_hook)
        
        # Restore print
        if is_hook:
            builtins.print = _print
    
    # Only show summary if not running as hook
    if not is_hook:
        print("=" * 50)
        print(f"✅ Protocols: {updated_count} updated, {skipped_count} skipped")
        print(f"✅ Memory scaffolding initialized for all agents")
    elif updated_count > 0:
        # Silent success message to stderr for hook mode
        print(f"Memory system initialized: {updated_count} agents updated", file=sys.stderr)
    
    # Check if memory structure exists (only show if not hook)
    if not is_hook:
        memory_dir = claude_dir / "memory" / "agents"
        if memory_dir.exists():
            print("\n📂 Memory Structure Check:")
            for agent_dir in memory_dir.iterdir():
                if agent_dir.is_dir():
                    trd_dir = agent_dir / "trds"
                    if trd_dir.exists():
                        trd_count = len(list(trd_dir.glob("*.md")))
                        print(f"  {agent_dir.name}: {trd_count} TRDs")
                    else:
                        print(f"  {agent_dir.name}: No TRD directory")

if __name__ == "__main__":
    # Support --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Initialize Complete Agent System")
        print("Usage: python3 initialize_agent_system.py")
        print("\nThis comprehensive hook (runs at SessionStart):")
        print("  - Parses agent names from YAML frontmatter")
        print("  - Adds TRD protocol to all agent definitions")
        print("  - Adds messaging protocol to all agent definitions")
        print("  - Ensures MCP messaging tools access for all agents")
        print("  - Creates complete memory directory structure")
        print("  - Initializes placeholder memory files for all agents")
        print("  - Sets up manager, team, and project directories")
        print("  - Creates cache directory for context files")
        print("  - Handles memory-manager specially (tools only, no protocols)")
        print("  - Preserves existing files (only creates missing ones)")
        print("  - Personalizes all protocols with correct agent names")
        sys.exit(0)
    
    main()