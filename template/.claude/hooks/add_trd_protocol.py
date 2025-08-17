#!/usr/bin/env python3
"""
SessionStart Hook: Initialize Agent Memory System

1. Adds TRD (Task Reflection Document) protocol to all agent definition files
2. Creates memory directory structure for all agents
3. Initializes placeholder memory files where needed
Runs silently at session start to ensure all agents are properly configured.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

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

## Handoffs Created
- [Work ready for other agents, or "None"]
- [Include specific file paths and next steps]
- [Format: "Ready for [agent]: [what] at [path]"]

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
- **Notable**: ~25% of tasks. Found something useful, created handoffs, or hit interesting issues
- **Significant**: ~5% of tasks. Major discoveries, architecture changes, or breakthrough solutions

This TRD is critical for team learning and knowledge sharing. Creating it helps future tasks build on your discoveries and avoid repeated mistakes.
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

def add_trd_to_agent(agent_path, agent_name):
    """Add TRD protocol to an agent definition file"""
    
    # Read current content
    with open(agent_path, 'r') as f:
        content = f.read()
    
    # Check if already has TRD protocol
    if has_trd_protocol(content):
        print(f"  ⏭️  {agent_name}: Already has TRD protocol")
        return False
    
    # Add TRD protocol at the end
    trd_section = get_trd_protocol(agent_name)
    new_content = content.rstrip() + trd_section
    
    # Write back
    with open(agent_path, 'w') as f:
        f.write(new_content)
    
    print(f"  ✅ {agent_name}: Added TRD protocol")
    return True

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
        agent_name = agent_file.stem
        
        # Skip memory-manager
        if agent_name == "memory-manager":
            if not is_hook:
                print(f"  ⏭️  {agent_name}: Skipped (memory-manager)")
            skipped_count += 1
            continue
        
        # Add TRD protocol (suppress output if running as hook)
        original_print = print if not is_hook else lambda *args, **kwargs: None
        
        # Temporarily replace print for the function call
        _print = print
        if is_hook:
            import builtins
            builtins.print = lambda *args, **kwargs: None
        
        if add_trd_to_agent(agent_file, agent_name):
            updated_count += 1
        else:
            skipped_count += 1
        
        # Always ensure memory scaffolding for all agents (except memory-manager)
        ensure_memory_scaffolding(agent_name, claude_dir, is_hook)
        
        # Restore print
        if is_hook:
            builtins.print = _print
    
    # Only show summary if not running as hook
    if not is_hook:
        print("=" * 50)
        print(f"✅ TRD Protocol: {updated_count} updated, {skipped_count} skipped")
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
        print("Initialize Agent Memory System")
        print("Usage: python3 add_trd_protocol.py")
        print("\nThis script (runs at SessionStart):")
        print("  - Adds TRD protocol to all agent definitions")
        print("  - Creates complete memory directory structure")
        print("  - Initializes placeholder memory files for all agents")
        print("  - Sets up manager, team, and project directories")
        print("  - Creates cache directory for context files")
        print("  - Skips memory-manager agent")
        print("  - Preserves existing files (only creates missing ones)")
        sys.exit(0)
    
    main()