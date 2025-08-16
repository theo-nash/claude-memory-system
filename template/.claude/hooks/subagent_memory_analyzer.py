#!/usr/bin/env python3
"""
Claude Code SubagentStop Hook: TRD Processing

Detects self-generated TRDs from subagents and triggers memory-manager processing.
Falls back to auto-generation if TRD not created.
"""

import json
import sys
import os
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path

def debug_log(message):
    """Log debug information"""
    try:
        debug_path = os.path.expanduser("~/.claude/subagentstop_debug.log")
        with open(debug_path, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except:
        pass

def get_claude_dir():
    """Detect if we're in project or global context using absolute paths"""
    # Get the current working directory from the hook data (if available)
    # or use the parent directories to find the project root
    
    # First, try to find .claude directory going up from current location
    current_dir = os.getcwd()
    
    # Check if we're in a subdirectory of a project with .claude
    check_dir = current_dir
    while check_dir != os.path.dirname(check_dir):  # Not root
        claude_project_dir = os.path.join(check_dir, ".claude")
        if os.path.exists(os.path.join(claude_project_dir, "agents", "memory-manager.md")):
            return claude_project_dir, "project", check_dir
        check_dir = os.path.dirname(check_dir)
    
    # Check current directory
    if os.path.exists(".claude/agents/memory-manager.md"):
        return ".claude", "project", os.getcwd()
    
    # Check global location
    global_claude_dir = os.path.expanduser("~/.claude")
    if os.path.exists(os.path.join(global_claude_dir, "agents", "memory-manager.md")):
        return global_claude_dir, "global", None
    
    return None, None, None

def get_wrapper_path(claude_dir, context_type, project_root):
    """Get the correct path to claude-memory wrapper"""
    if context_type == "project":
        if project_root:
            # Use absolute path to project root + claude-memory
            wrapper_path = os.path.join(project_root, "claude-memory")
        else:
            # Fallback: relative from .claude directory
            wrapper_path = os.path.join(os.path.dirname(claude_dir), "claude-memory")
    else:
        # Global installation
        wrapper_path = os.path.expanduser("~/.local/bin/claude-memory")
    
    return wrapper_path

def read_hook_input_robust():
    """
    Multiple approaches to read stdin reliably
    """
    debug_log("Starting stdin read...")
    
    # Check if stdin is a TTY (shouldn't be for hooks)
    if sys.stdin.isatty():
        debug_log("ERROR: stdin is TTY")
        return None, "stdin is TTY"
    
    try:
        # Method 1: Read all available data
        debug_log("Reading stdin...")
        import select
        
        # Wait up to 5 seconds for stdin data
        ready, _, _ = select.select([sys.stdin], [], [], 5.0)
        if not ready:
            debug_log("ERROR: No stdin data available after 5 seconds")
            return None, "stdin timeout"
        
        # Read the data
        stdin_content = sys.stdin.read()
        debug_log(f"Read {len(stdin_content)} characters from stdin")
        
        if not stdin_content or not stdin_content.strip():
            debug_log("ERROR: stdin content is empty")
            return None, "stdin empty"
        
        debug_log(f"Stdin content preview: {stdin_content[:200]}...")
        
        # Parse JSON
        hook_data = json.loads(stdin_content.strip())
        debug_log(f"Successfully parsed JSON: {list(hook_data.keys())}")
        return hook_data, None
        
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        return None, f"JSON decode error: {e}"
    except Exception as e:
        debug_log(f"Stdin read error: {e}")
        return None, f"stdin read error: {e}"

def extract_subagent_info_from_transcript(transcript_path):
    """
    Extract subagent name and session ID from transcript
    """
    debug_log(f"Analyzing transcript: {transcript_path}")
    
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        debug_log(f"Transcript has {len(lines)} lines")
        
        # Look for ALL Task tool calls, then get the most recent one
        task_calls = []
        
        for i, line in enumerate(lines):
            try:
                entry = json.loads(line)
                
                # Check for Task tool in message content
                message = entry.get('message', {})
                content = message.get('content', [])
                
                if isinstance(content, list):
                    for content_item in content:
                        if (isinstance(content_item, dict) and 
                            content_item.get('name') == 'Task'):
                            
                            task_input = content_item.get('input', {})
                            subagent_type = task_input.get('subagent_type', '')
                            
                            if subagent_type:
                                # Try to extract session ID from the entry
                                session_id = entry.get('session_id', '')
                                task_calls.append({
                                    'line': i,
                                    'subagent_type': subagent_type,
                                    'session_id': session_id,
                                    'prompt': task_input.get('prompt', '')[:100] + '...',
                                    'timestamp': entry.get('timestamp', '')
                                })
                                debug_log(f"Found Task call on line {i}: {subagent_type}")
                            
            except json.JSONDecodeError:
                continue
        
        debug_log(f"Found {len(task_calls)} Task calls total")
        
        if task_calls:
            # Return the most recent (last) subagent call
            most_recent = task_calls[-1]
            debug_log(f"Most recent subagent: {most_recent['subagent_type']}")
            return most_recent['subagent_type'], most_recent.get('session_id', '')
        
        debug_log("No Task calls found in transcript")
        return None, None
        
    except Exception as e:
        debug_log(f"Error analyzing transcript: {e}")
        return None, None

def simple_transcript_analysis_enhanced(transcript_path, subagent_name):
    """Enhanced simple analysis with better insight extraction"""
    debug_log(f"Performing analysis for {subagent_name}")
    
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        tools_used = set()
        memory_operations = []
        errors = 0
        assistant_messages = []
        
        # Track the subagent session specifically
        in_subagent_session = False
        subagent_tools = []
        
        for line in lines:
            try:
                entry = json.loads(line)
                
                # Check if this line is part of subagent session (isSidechain: true)
                is_sidechain = entry.get('isSidechain', False)
                
                # Look for tool usage
                message = entry.get('message', {})
                content = message.get('content', [])
                
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            # Tool usage
                            if item.get('type') == 'tool_use':
                                tool_name = item.get('name', '')
                                if tool_name:
                                    tools_used.add(tool_name)
                                    if is_sidechain:
                                        subagent_tools.append(tool_name)
                            
                            # Assistant text
                            elif item.get('type') == 'text' and is_sidechain:
                                text = item.get('text', '')
                                if len(text) > 50:  # Substantial content
                                    assistant_messages.append(text[:150])
                
                # Look for memory operations
                if 'claude-memory' in line:
                    memory_operations.append("Memory operation detected")
                
                # Count errors
                if '"is_error":true' in line:
                    errors += 1
                    
            except json.JSONDecodeError:
                continue
        
        # Generate comprehensive analysis
        analysis_parts = []
        
        analysis_parts.append(f"SUBAGENT SESSION ANALYSIS for {subagent_name}")
        analysis_parts.append(f"Session completed at {datetime.now().isoformat()}")
        analysis_parts.append("")
        
        if tools_used:
            analysis_parts.append(f"TOOLS USED: {', '.join(sorted(tools_used))}")
        
        if subagent_tools:
            analysis_parts.append(f"SUBAGENT TOOLS: {', '.join(subagent_tools)}")
        
        analysis_parts.append(f"MEMORY OPERATIONS: {len(memory_operations)}")
        analysis_parts.append(f"ERRORS ENCOUNTERED: {errors}")
        
        if assistant_messages:
            analysis_parts.append("")
            analysis_parts.append("KEY OUTPUTS:")
            for i, msg in enumerate(assistant_messages[:3], 1):
                analysis_parts.append(f"{i}. {msg}...")
        
        # Add insights based on subagent type
        if subagent_name == 'task-executor':
            analysis_parts.append("")
            analysis_parts.append("TASK-EXECUTOR INSIGHTS:")
            if 'TodoWrite' in tools_used:
                analysis_parts.append("- Successfully used TODO list management")
            if errors == 0:
                analysis_parts.append("- Completed task without errors")
            else:
                analysis_parts.append(f"- Encountered {errors} errors during execution")
        
        return "\n".join(analysis_parts)
        
    except Exception as e:
        debug_log(f"Analysis error: {e}")
        return f"Subagent {subagent_name} session completed (analysis failed: {e})"

def cleanup_cache_file(subagent_name, session_id, claude_dir):
    """
    Clean up the context cache file for this subagent session
    """
    try:
        # Generate the cache filename using same logic as PreToolUse hook
        _hash = hashlib.md5((subagent_name + session_id).encode('utf-8')).hexdigest()[:6]
        cache_filename = f"{_hash}.md"
        cache_path = os.path.join(claude_dir, "cache", cache_filename)
        
        if os.path.exists(cache_path):
            os.remove(cache_path)
            debug_log(f"Cleaned up cache file: {cache_path}")
            return True
        else:
            debug_log(f"Cache file not found (already deleted?): {cache_path}")
            return False
    except Exception as e:
        debug_log(f"Error cleaning up cache file: {e}")
        return False

def find_latest_trd(subagent_name, claude_dir, session_id):
    """
    Check if subagent created a TRD for this session
    Returns (trd_path, created_recently) tuple
    """
    import glob
    from datetime import datetime, timedelta
    
    trd_dir = os.path.join(claude_dir, "memory", "agents", subagent_name, "trds")
    
    if not os.path.exists(trd_dir):
        debug_log(f"TRD directory doesn't exist: {trd_dir}")
        return None, False
    
    # Look for TRDs created in the last few minutes
    # Pattern: trd-YYYY-MM-DD-HHMM-*.md or trd-*-{session_id[:8]}.md
    patterns = [
        os.path.join(trd_dir, f"trd-*-{session_id[:8]}.md") if session_id else None,
        os.path.join(trd_dir, "trd-*.md")
    ]
    
    trd_files = []
    for pattern in patterns:
        if pattern:
            trd_files.extend(glob.glob(pattern))
    
    if not trd_files:
        debug_log(f"No TRD files found in {trd_dir}")
        return None, False
    
    # Get the most recent TRD
    latest_trd = max(trd_files, key=os.path.getmtime)
    
    # Check if it was created recently (within last 5 minutes)
    file_time = datetime.fromtimestamp(os.path.getmtime(latest_trd))
    time_diff = datetime.now() - file_time
    created_recently = time_diff < timedelta(minutes=5)
    
    debug_log(f"Found TRD: {latest_trd} (created {time_diff.seconds}s ago)")
    
    return latest_trd, created_recently

def call_memory_manager_for_trd(wrapper_path, subagent_name, trd_path, claude_dir):
    """Call memory-manager to process a self-generated TRD"""
    debug_log(f"Processing TRD for {subagent_name}: {trd_path}")
    
    try:
        # Just pass the TRD file path - memory-manager will read it
        # Call memory-manager via wrapper
        if claude_dir != os.path.expanduser("~/.claude"):
            wrapper_cwd = os.path.dirname(os.path.abspath(claude_dir))
        else:
            wrapper_cwd = os.getcwd()
        
        result = subprocess.run(
            [wrapper_path, 'process-trd', subagent_name, trd_path],
            capture_output=True,
            text=True,
            cwd=wrapper_cwd,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "TRD processed successfully"
        else:
            return False, f"TRD processing failed: {result.stderr}"
            
    except Exception as e:
        debug_log(f"TRD processing error: {e}")
        return False, f"TRD processing error: {e}"

def call_claude_memory_wrapper(wrapper_path, subagent_name, analysis_content, claude_dir):
    """Use the existing claude-memory wrapper for fallback auto-generation"""
    debug_log(f"Calling claude-memory wrapper for {subagent_name} (fallback)")
    
    try:        
        debug_log(f"Wrapper path: {wrapper_path}")
        
        if not os.path.exists(wrapper_path):
            debug_log(f"Wrapper not found at {wrapper_path}")
            return False, f"claude-memory wrapper not found"
        
        # Call the wrapper with correct working directory
        # For project contexts, use project_root; for global, use current directory
        if claude_dir != os.path.expanduser("~/.claude"):  # Project context
            # Use project root directory as working directory
            wrapper_cwd = os.path.dirname(os.path.abspath(claude_dir))
        else:  # Global context
            wrapper_cwd = os.getcwd()
        
        debug_log(f"Wrapper working directory: {wrapper_cwd}")
        
        result = subprocess.run(
            [wrapper_path, 'update-memories', subagent_name, analysis_content],
            capture_output=True,
            text=True,
            cwd=wrapper_cwd,
            timeout=300
        )
        
        debug_log(f"Wrapper result: {result.returncode}")
        if result.stdout:
            debug_log(f"Wrapper stdout: {result.stdout[:200]}...")
        if result.stderr:
            debug_log(f"Wrapper stderr: {result.stderr[:200]}...")
        
        if result.returncode == 0:
            return True, "Analysis completed via claude-memory wrapper"
        else:
            return False, f"claude-memory wrapper failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        debug_log("Wrapper timeout")
        return False, "claude-memory wrapper timed out"
    except Exception as e:
        debug_log(f"Wrapper error: {e}")
        return False, f"claude-memory wrapper error: {e}"

def main():
    """Main hook execution function"""
    debug_log("=== SubagentStop hook started ===")
    
    try:
        # Handle direct execution (testing)
        if len(sys.argv) > 1 and sys.argv[1] in ['--test', '--help']:
            if '--help' in sys.argv:
                print("Claude Code SubagentStop Hook - Complete Implementation")
                print("Logs debug info to ~/.claude/subagentstop_debug.log")
                return
            elif '--test' in sys.argv:
                debug_log("TEST MODE EXECUTED")
                print(f"[{datetime.now().isoformat()}] SubagentStop hook test successful!")
                print("Debug log: ~/.claude/subagentstop_debug.log")
                return
        
        # Read hook input with robust method
        hook_data, error = read_hook_input_robust()
        
        if error:
            debug_log(f"Hook input error: {error}")
            print(f"Hook input error: {error}", file=sys.stderr)
            sys.exit(0)
        
        # Extract session information
        session_id = hook_data.get('session_id', '')
        transcript_path = hook_data.get('transcript_path', '')
        hook_event_name = hook_data.get('hook_event_name', '')
        
        debug_log(f"Session: {session_id[:8]}...")
        debug_log(f"Transcript: {transcript_path}")
        debug_log(f"Event: {hook_event_name}")
        
        # Verify this is a SubagentStop event
        if hook_event_name != 'SubagentStop':
            debug_log(f"Wrong event type: {hook_event_name}")
            sys.exit(0)
        
        # Verify transcript exists
        if not transcript_path or not os.path.exists(transcript_path):
            debug_log(f"Transcript not found: {transcript_path}")
            sys.exit(0)
        
        # Detect Claude directory and context
        claude_dir, context_type, project_root = get_claude_dir()
        if not claude_dir:
            debug_log("Memory system not found")
            sys.exit(0)
        
        debug_log(f"Memory context: {context_type}")
        
        # Extract subagent name and session info from transcript
        subagent_name, transcript_session_id = extract_subagent_info_from_transcript(transcript_path)
        if not subagent_name:
            debug_log("Could not identify subagent")
            sys.exit(0)
        
        # Skip memory-manager itself
        if subagent_name == 'memory-manager':
            debug_log("Skipping memory-manager recursion")
            sys.exit(0)
        
        debug_log(f"Processing subagent: {subagent_name}")
        
        # Check if subagent created a TRD
        trd_path, trd_is_recent = find_latest_trd(subagent_name, claude_dir, session_id or transcript_session_id)
        
        wrapper_path = get_wrapper_path(claude_dir, context_type, project_root)
        
        if trd_path and trd_is_recent:
            # Subagent created their own TRD - process it
            debug_log(f"Found self-generated TRD: {trd_path}")
            print(f"📝 Processing self-generated TRD for {subagent_name}...", file=sys.stderr)
            
            success, message = call_memory_manager_for_trd(wrapper_path, subagent_name, trd_path, claude_dir)
            
            if success:
                debug_log("SUCCESS: TRD processed")
                print(f"✅ TRD processed for {subagent_name}", file=sys.stderr)
                print(f"   TRD: {os.path.basename(trd_path)}", file=sys.stderr)
            else:
                debug_log(f"TRD processing failed: {message}")
                print(f"⚠️  TRD processing failed, falling back to auto-generation", file=sys.stderr)
                # Fall back to auto-generation
                analysis_content = simple_transcript_analysis_enhanced(transcript_path, subagent_name)
                success, message = call_claude_memory_wrapper(wrapper_path, subagent_name, analysis_content, claude_dir)
        else:
            # No TRD found - fall back to auto-generation with warning
            if trd_path and not trd_is_recent:
                debug_log(f"Found old TRD (not recent): {trd_path}")
                print(f"⚠️  Found old TRD for {subagent_name}, generating fresh analysis", file=sys.stderr)
            else:
                debug_log("No TRD found - using auto-generation")
                print(f"⚠️  No TRD found for {subagent_name} - using auto-generation", file=sys.stderr)
                print(f"   Reminder: Agents should create TRDs before completing tasks", file=sys.stderr)
            
            # Generate analysis from transcript
            analysis_content = simple_transcript_analysis_enhanced(transcript_path, subagent_name)
            debug_log(f"Generated analysis: {len(analysis_content)} characters")
            
            success, message = call_claude_memory_wrapper(wrapper_path, subagent_name, analysis_content, claude_dir)
            
            if success:
                debug_log("SUCCESS: Auto-generated memory analysis completed")
                print(f"✅ Auto-generated memory analysis for {subagent_name}", file=sys.stderr)
            else:
                debug_log(f"FAILED: {message}")
                print(f"❌ Memory analysis failed for {subagent_name}: {message}", file=sys.stderr)
        
        # Clean up the context cache file (if it exists)
        cleanup_cache_file(subagent_name, session_id, claude_dir)
        
        debug_log("=== SubagentStop hook completed ===")
        sys.exit(0)
        
    except Exception as e:
        debug_log(f"CRITICAL ERROR: {e}")
        print(f"SubagentStop hook error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
