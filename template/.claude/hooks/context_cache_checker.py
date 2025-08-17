#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Context Cache Checker

Checks if context cache exists for the target subagent/task.
If no cache exists, instructs main agent to call memory-manager first.
"""

import json
import sys
import select
import os
import hashlib
from datetime import datetime

def has_stdin_data(timeout=0.1):
    """Check if there's data available on stdin without blocking"""
    if select.select([sys.stdin], [], [], timeout) == ([sys.stdin], [], []):
        return True
    return False

def get_claude_dir():
    """Detect if we're in project or global context"""
    current_dir = os.getcwd()
    
    check_dir = current_dir
    while check_dir != os.path.dirname(check_dir):
        claude_project_dir = os.path.join(check_dir, ".claude")
        if os.path.exists(os.path.join(claude_project_dir, "agents", "memory-manager.md")):
            return claude_project_dir, "project", check_dir
        check_dir = os.path.dirname(check_dir)
    
    if os.path.exists(".claude/agents/memory-manager.md"):
        return ".claude", "project", os.getcwd()
    
    global_claude_dir = os.path.expanduser("~/.claude")
    if os.path.exists(os.path.join(global_claude_dir, "agents", "memory-manager.md")):
        return global_claude_dir, "global", None
    
    return None, None, None

def generate_cache_filename(subagent_type, session_id):
    _hash = hashlib.md5((subagent_type + session_id).encode('utf-8')).hexdigest()[:6]
    return f"{_hash}.md"

def check_cache_exists(subagent_type, session_id, claude_dir):
    """Check if context cache file exists for this subagent/task"""
    cache_filename = generate_cache_filename(subagent_type, session_id)
    cache_path = os.path.join(claude_dir, "cache", cache_filename)
    
    return os.path.exists(cache_path), cache_path
    
def main():
    """Main hook execution function"""
    try:
        # Handle direct execution (testing)
        if len(sys.argv) > 1 and sys.argv[1] in ['--test', '--help']:
            if '--help' in sys.argv:
                print("Claude Code Context Cache Checker Hook (PreToolUse)")
                print("Usage: Called automatically by Claude Code PreToolUse system")
                print("Test: python3 context_cache_checker.py --test")
                print("Note: Memory storage is automatic via SubagentStop hook")
                return
            elif '--test' in sys.argv:
                print(f"[{datetime.now().isoformat()}] PreToolUse hook is working!")
                print("Context cache checking: ACTIVE")
                print("Memory storage: HANDLED BY SUBAGENTSTOP")
                return
        
        # Check if we have stdin data (normal hook operation)
        if not has_stdin_data():
            print("No stdin data available - hook script exiting gracefully", file=sys.stderr)
            sys.exit(0)
        
        # Read hook data from stdin
        hook_data = json.load(sys.stdin)
        
        # Extract Task tool parameters
        tool_input = hook_data.get('tool_input', {})
        subagent_type = tool_input.get('subagent_type', '')
        prompt = tool_input.get('prompt', '')
        session_id = hook_data.get('session_id', 'unknown')
        
        # Only check cache for valid subagent calls
        if not subagent_type or not prompt:
            sys.exit(0)
        
        # Skip if this IS the memory-manager
        if subagent_type == 'memory-manager':
            sys.exit(0)
        
        # Detect Claude directory and context
        claude_dir, context_type, project_root = get_claude_dir()
        if not claude_dir:
            print("Memory system not found - skipping context cache check", file=sys.stderr)
            sys.exit(0)
        
        # Check if context cache exists
        cache_exists, cache_path = check_cache_exists(subagent_type, session_id, claude_dir)
        
        if not cache_exists:
            # No cache - instruct main agent to call memory-manager first
            guidance = f"""
CONTEXT CACHE REQUIRED FOR {subagent_type.upper()}:

Before calling the {subagent_type} subagent, please generate a context cache:

1. First call the memory-manager:
   Use Task tool with subagent_type: "memory-manager"
   Prompt: "Build a task-specific context cache for {subagent_type} at {generate_cache_filename(subagent_type, session_id)}. The agent's task is [short description of agent's task]"

2. Then retry calling {subagent_type}:
    Your prompt to the subagent MUST include these instructions:
    
    "CRITICAL: Before starting any work:
    1. Read the context cache at {generate_cache_filename(subagent_type, session_id)}
    2. Explore ALL files listed in the 'Recommended Reading' section - these contain crucial details for your task
    3. Use this context to guide your entire approach
    
    [Your actual task instructions here]"
    
    This ensures {subagent_type} has full context and explores all relevant knowledge before starting.
"""
            
            print(guidance, file=sys.stderr)
            sys.exit(2)  # Block the call and provide feedback
        
        # Cache exists - now check if TRD reminder is included
        trd_filename = f"trd-{datetime.now().strftime('%Y-%m-%d-%H%M')}-{session_id[:8]}.md"
        if "TRD" not in prompt and "Task Reflection Document" not in prompt:
            # Missing TRD reminder - block and provide guidance
            guidance = f"""
TRD REMINDER REQUIRED FOR {subagent_type.upper()}:

Please include a reminder in your prompt for the subagent to create their Task Reflection Document.

Add this to your prompt:
"Remember to create a TRD at .claude/memory/agents/{subagent_type}/trds/{trd_filename} before completing your task."

Then retry calling {subagent_type}.
"""
            
            print(guidance, file=sys.stderr)
            sys.exit(2)  # Block the call and provide feedback
        
        # Both cache exists and TRD reminder present - proceed
        print(f"✅ Context cache ready at {cache_path}", file=sys.stderr)
        print(f"✅ TRD reminder included for {subagent_type}", file=sys.stderr)
        sys.exit(0)  # Allow the Task call to proceed
        
    except json.JSONDecodeError as e:
        print(f"Hook JSON decode error: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # Don't block on errors
        print(f"Context cache check error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
