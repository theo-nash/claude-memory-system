#!/usr/bin/env python3
"""
Enhanced Transcript Parser for Claude Code Memory System

Converts JSONL transcript into LLM-friendly format for memory-manager analysis.
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

def parse_transcript_to_readable_format(transcript_path: str) -> str:
    """
    Parse Claude Code JSONL transcript into human/LLM readable format
    """
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        events = []
        for line in lines:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except json.JSONDecodeError:
                continue
        
        # Extract key information
        session_info = extract_session_info(events)
        subagent_info = extract_subagent_info(events)
        conversation_flow = extract_conversation_flow(events)
        tool_usage = extract_tool_usage(events)
        outcomes = extract_outcomes(events)
        
        # Generate readable report
        report = generate_readable_report(
            session_info, subagent_info, conversation_flow, tool_usage, outcomes
        )
        
        return report
        
    except Exception as e:
        return f"Error parsing transcript: {e}"

def extract_session_info(events: List[Dict]) -> Dict:
    """Extract basic session metadata"""
    first_event = events[0] if events else {}
    last_event = events[-1] if events else {}
    
    return {
        'session_id': first_event.get('sessionId', 'unknown'),
        'start_time': first_event.get('timestamp', ''),
        'end_time': last_event.get('timestamp', ''),
        'duration_minutes': calculate_duration(first_event.get('timestamp'), last_event.get('timestamp')),
        'total_events': len(events),
        'working_directory': first_event.get('cwd', ''),
        'git_branch': first_event.get('gitBranch', 'unknown')
    }

def extract_subagent_info(events: List[Dict]) -> Optional[Dict]:
    """Extract subagent identification and initial request"""
    for event in events:
        if event.get('type') == 'user':
            message = event.get('message', {})
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, str) and ('FIRST ACTION' in content or 'claude-memory' in content):
                    return {
                        'initial_request': content,
                        'appears_to_be_subagent': True,
                        'has_memory_workflow': 'claude-memory' in content
                    }
    
    # Check for Task tool usage in parent events
    for event in events:
        if (event.get('message', {}).get('content') and 
            isinstance(event['message']['content'], list)):
            for content_item in event['message']['content']:
                if (isinstance(content_item, dict) and 
                    content_item.get('name') == 'Task'):
                    return {
                        'subagent_type': content_item.get('input', {}).get('subagent_type', 'unknown'),
                        'subagent_prompt': content_item.get('input', {}).get('prompt', ''),
                        'appears_to_be_subagent': True
                    }
    
    return {'appears_to_be_subagent': False}

def extract_conversation_flow(events: List[Dict]) -> List[Dict]:
    """Extract the main conversation flow"""
    flow = []
    
    for event in events:
        if event.get('type') == 'user':
            # User message
            message = event.get('message', {})
            content = message.get('content', '')
            
            if isinstance(content, str):
                flow.append({
                    'type': 'user_message',
                    'timestamp': event.get('timestamp', ''),
                    'content': content[:500] + '...' if len(content) > 500 else content,
                    'is_initial_request': len(flow) == 0
                })
            elif isinstance(content, list):
                # Tool result
                for item in content:
                    if item.get('type') == 'tool_result':
                        tool_content = item.get('content', '')
                        if isinstance(tool_content, str) and tool_content.strip():
                            flow.append({
                                'type': 'tool_result',
                                'timestamp': event.get('timestamp', ''),
                                'tool_use_id': item.get('tool_use_id', ''),
                                'content': tool_content[:300] + '...' if len(tool_content) > 300 else tool_content,
                                'is_error': item.get('is_error', False)
                            })
        
        elif event.get('type') == 'assistant':
            # Assistant message
            message = event.get('message', {})
            content = message.get('content', [])
            
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text = item.get('text', '')
                        if text.strip():
                            flow.append({
                                'type': 'assistant_message',
                                'timestamp': event.get('timestamp', ''),
                                'content': text[:400] + '...' if len(text) > 400 else text
                            })
                    
                    elif item.get('type') == 'tool_use':
                        flow.append({
                            'type': 'tool_use',
                            'timestamp': event.get('timestamp', ''),
                            'tool_name': item.get('name', ''),
                            'tool_input': item.get('input', {}),
                            'description': item.get('input', {}).get('description', '')
                        })
    
    return flow

def extract_tool_usage(events: List[Dict]) -> Dict:
    """Extract and summarize tool usage"""
    tools_used = {}
    
    for event in events:
        if event.get('type') == 'assistant':
            message = event.get('message', {})
            content = message.get('content', [])
            
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown')
                    tool_input = item.get('input', {})
                    
                    if tool_name not in tools_used:
                        tools_used[tool_name] = []
                    
                    tools_used[tool_name].append({
                        'timestamp': event.get('timestamp', ''),
                        'input': tool_input,
                        'description': tool_input.get('description', '')
                    })
    
    return tools_used

def extract_outcomes(events: List[Dict]) -> Dict:
    """Extract final outcomes and results"""
    outcomes = {
        'completed_successfully': False,
        'errors_encountered': [],
        'final_state': '',
        'memory_operations': [],
        'files_modified': [],
        'commands_executed': []
    }
    
    # Look for completion indicators
    for event in reversed(events):  # Check from end
        if event.get('type') == 'assistant':
            message = event.get('message', {})
            content = message.get('content', [])
            
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '').lower()
                    if any(indicator in text for indicator in ['completed', 'finished', 'done', '✅']):
                        outcomes['completed_successfully'] = True
                        outcomes['final_state'] = item.get('text', '')[:300]
                        break
            if outcomes['final_state']:
                break
    
    # Extract memory operations
    for event in events:
        if event.get('type') == 'assistant':
            message = event.get('message', {})
            content = message.get('content', [])
            
            for item in content:
                if (isinstance(item, dict) and 
                    item.get('type') == 'tool_use' and 
                    item.get('name') == 'Bash'):
                    
                    command = item.get('input', {}).get('command', '')
                    if 'claude-memory' in command:
                        outcomes['memory_operations'].append(command)
                    else:
                        outcomes['commands_executed'].append(command)
                
                elif (isinstance(item, dict) and 
                      item.get('type') == 'tool_use' and 
                      item.get('name') in ['Write', 'Edit', 'MultiEdit']):
                    
                    file_path = item.get('input', {}).get('file_path', '')
                    if file_path:
                        outcomes['files_modified'].append(file_path)
    
    # Extract errors
    for event in events:
        if event.get('type') == 'user':
            message = event.get('message', {})
            content = message.get('content', [])
            
            if isinstance(content, list):
                for item in content:
                    if (isinstance(item, dict) and 
                        item.get('type') == 'tool_result' and 
                        item.get('is_error')):
                        outcomes['errors_encountered'].append(item.get('content', ''))
    
    return outcomes

def calculate_duration(start_time: str, end_time: str) -> float:
    """Calculate duration in minutes"""
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        return round((end - start).total_seconds() / 60, 1)
    except:
        return 0.0

def generate_readable_report(session_info: Dict, subagent_info: Dict, 
                           conversation_flow: List[Dict], tool_usage: Dict, 
                           outcomes: Dict) -> str:
    """Generate the final LLM-friendly report"""
    
    report = f"""# SUBAGENT SESSION ANALYSIS

## SESSION OVERVIEW
- **Session ID**: {session_info['session_id'][:8]}...
- **Duration**: {session_info['duration_minutes']} minutes
- **Working Directory**: {session_info['working_directory']}
- **Git Branch**: {session_info['git_branch']}
- **Events**: {session_info['total_events']}

## SUBAGENT CONTEXT
"""
    
    if subagent_info.get('appears_to_be_subagent'):
        if 'subagent_type' in subagent_info:
            report += f"- **Type**: {subagent_info['subagent_type']}\n"
            report += f"- **Task**: {subagent_info['subagent_prompt'][:200]}...\n"
        else:
            report += "- **Type**: Subagent session detected\n"
            report += f"- **Memory Workflow**: {subagent_info.get('has_memory_workflow', False)}\n"
    else:
        report += "- **Type**: Regular session\n"
    
    report += f"\n## TOOLS USED\n"
    for tool, usages in tool_usage.items():
        report += f"- **{tool}**: {len(usages)} times\n"
        for usage in usages[:2]:  # Show first 2 usages
            if usage['description']:
                report += f"  - {usage['description']}\n"
            elif tool == 'Bash' and 'command' in usage['input']:
                report += f"  - Command: {usage['input']['command']}\n"
    
    report += f"\n## OUTCOMES\n"
    report += f"- **Success**: {outcomes['completed_successfully']}\n"
    report += f"- **Errors**: {len(outcomes['errors_encountered'])}\n"
    
    if outcomes['memory_operations']:
        report += f"- **Memory Ops**: {len(outcomes['memory_operations'])}\n"
    
    if outcomes['files_modified']:
        report += f"- **Files Modified**: {len(outcomes['files_modified'])}\n"
    
    if outcomes['final_state']:
        report += f"\n## COMPLETION STATUS\n{outcomes['final_state']}\n"
    
    # Add key conversation highlights
    report += f"\n## SESSION HIGHLIGHTS\n"
    key_events = [event for event in conversation_flow 
                 if event['type'] in ['user_message', 'assistant_message']][:5]
    for i, event in enumerate(key_events, 1):
        speaker = "User" if event['type'] == 'user_message' else "Assistant"
        content = event['content'][:150] + "..." if len(event['content']) > 150 else event['content']
        report += f"{i}. **{speaker}**: {content}\n\n"
    
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
        readable_report = parse_transcript_to_readable_format(transcript_path)
        print(readable_report)
    else:
        print("Usage: python3 transcript_parser.py <transcript_path>")
