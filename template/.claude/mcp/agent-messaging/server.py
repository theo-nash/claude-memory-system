#!/usr/bin/env python3
"""
Agent Messaging MCP Server
Provides tools for inter-agent communication within Claude Code
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Initialize server
app = Server("agent-messaging")

# Configuration
MESSAGES_DIR = os.getenv("MESSAGES_DIR", ".claude/messages")

def ensure_messages_dir():
    """Ensure messages directory structure exists"""
    Path(MESSAGES_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{MESSAGES_DIR}/archive").mkdir(parents=True, exist_ok=True)

def parse_agent_file(file_path: Path) -> Optional[Dict[str, str]]:
    """Parse agent file to extract name and description from frontmatter"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for YAML frontmatter
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
        frontmatter_lines = lines[1:end_index]
        name = None
        description = None
        
        for line in frontmatter_lines:
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                description = line.split(':', 1)[1].strip()
                
        if name:
            return {
                'name': name,
                'description': description or 'No description available',
                'file': file_path.stem
            }
    except Exception:
        pass
    return None

def get_available_agents() -> Dict[str, Dict[str, str]]:
    """Dynamically discover all available agents from .claude/agents directory
    Returns dict mapping agent name to info (description, file)"""
    # Try multiple possible locations
    possible_dirs = [
        Path(".claude/agents"),
        Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "agents",
        Path.home() / ".claude" / "agents"
    ]
    
    agents = {}
    for dir_path in possible_dirs:
        if dir_path.exists() and dir_path.is_dir():
            for agent_file in dir_path.glob("*.md"):
                # Skip example and template files
                if agent_file.stem.startswith("_") or "example" in agent_file.stem.lower():
                    continue
                    
                # Parse the agent file
                agent_info = parse_agent_file(agent_file)
                if agent_info:
                    # Use the name from frontmatter, not filename
                    agents[agent_info['name']] = agent_info
    
    # Always include memory-manager if not found
    if "memory-manager" not in agents:
        agents["memory-manager"] = {
            'name': 'memory-manager',
            'description': 'Lightweight memory coordinator for Claude Code subagents',
            'file': 'memory-manager'
        }
    
    return agents

def load_messages(agent_name: str) -> List[Dict]:
    """Load messages for a specific agent"""
    message_file = Path(MESSAGES_DIR) / f"{agent_name}.json"
    
    if not message_file.exists():
        return []
    
    try:
        with open(message_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_messages(agent_name: str, messages: List[Dict]):
    """Save messages for a specific agent"""
    message_file = Path(MESSAGES_DIR) / f"{agent_name}.json"
    
    with open(message_file, 'w') as f:
        json.dump(messages, f, indent=2, default=str)

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available messaging tools"""
    # Get dynamic list of agents for helpful descriptions
    available_agents = get_available_agents()
    agent_names = sorted(available_agents.keys())
    agents_hint = ", ".join(agent_names[:5]) + ("..." if len(agent_names) > 5 else "")
    
    return [
        types.Tool(
            name="create_message",
            description=f"Send a message to another agent. Known agents include: {agents_hint}",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_agent": {
                        "type": "string",
                        "description": "Your agent name (sender). If you don't know your name, use a descriptive identifier."
                    },
                    "to_agent": {
                        "type": "string",
                        "description": f"Recipient agent name. Known agents: {agents_hint}"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message content. Be specific with examples, code, or findings"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Message priority level",
                        "default": "medium"
                    },
                    "context_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file paths the recipient should review",
                        "default": []
                    }
                },
                "required": ["from_agent", "to_agent", "message"]
            }
        ),
        types.Tool(
            name="read_messages",
            description="Read messages sent to you by other agents",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Your agent name (whose messages to read). Use same name as when sending."
                    },
                    "mark_as_read": {
                        "type": "boolean",
                        "description": "Mark messages as read after retrieving",
                        "default": True
                    },
                    "priority_filter": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Only show messages of specific priority"
                    },
                    "include_read": {
                        "type": "boolean",
                        "description": "Include already-read messages in response",
                        "default": False
                    }
                },
                "required": ["agent_name"]
            }
        ),
        types.Tool(
            name="clear_messages",
            description="Archive old read messages to clean up inbox",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Your agent name (whose messages to clear)"
                    },
                    "older_than_days": {
                        "type": "integer",
                        "description": "Archive messages older than this many days",
                        "default": 7
                    }
                },
                "required": ["agent_name"]
            }
        ),
        types.Tool(
            name="list_agents",
            description="Get a list of all available agents you can message",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls"""
    ensure_messages_dir()
    
    if name == "create_message":
        return await create_message(arguments)
    elif name == "read_messages":
        return await read_messages(arguments)
    elif name == "clear_messages":
        return await clear_messages(arguments)
    elif name == "list_agents":
        return await list_agents(arguments)
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def create_message(args: Dict[str, Any]) -> list[types.TextContent]:
    """Create and send a message to another agent"""
    from_agent = args["from_agent"]
    to_agent = args["to_agent"]
    message_text = args["message"]
    priority = args.get("priority", "medium")
    context_files = args.get("context_files", [])
    
    # Get all available agents
    available_agents = get_available_agents()
    agent_names = set(available_agents.keys())
    
    # Check if recipient exists
    if to_agent not in agent_names:
        # Find similar agent names for suggestions
        similar = [name for name in agent_names if 
                  to_agent.lower() in name.lower() or 
                  name.lower() in to_agent.lower() or
                  any(part in name.lower() for part in to_agent.lower().split('-'))]
        
        # Build helpful error message with full agent list
        error_msg = [f"❌ Agent '{to_agent}' not found.\n"]
        
        if similar:
            error_msg.append(f"\n💡 Did you mean one of these?\n")
            for agent_name in similar[:3]:
                agent_info = available_agents[agent_name]
                error_msg.append(f"   • {agent_name} - {agent_info['description'][:60]}...\n")
        
        error_msg.append(f"\n📋 Available agents:\n")
        for agent_name in sorted(agent_names):
            agent_info = available_agents[agent_name]
            error_msg.append(f"   • {agent_name} - {agent_info['description'][:60]}...\n")
        
        error_msg.append(f"\n🔄 Please retry with: create_message(from_agent=\"{from_agent}\", to_agent=\"<correct-agent-name>\", ...)")
        
        return [types.TextContent(
            type="text",
            text="".join(error_msg)
        )]
    
    # Also validate sender exists and warn if not
    sender_warning = ""
    if from_agent not in agent_names:
        sender_warning = f"\n⚠️  Note: Sender '{from_agent}' not in agent list. Consider using a known agent name for better tracking."
    
    # Create message entry
    message_entry = {
        "id": f"msg-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{from_agent[:8] if len(from_agent) >= 8 else from_agent}",
        "from": from_agent,
        "to": to_agent,
        "timestamp": datetime.now().isoformat(),
        "priority": priority,
        "message": message_text,
        "context_files": context_files,
        "read": False
    }
    
    # Load existing messages for recipient
    messages = load_messages(to_agent)
    
    # Add new message
    messages.append(message_entry)
    
    # Sort by priority (high first) and timestamp
    priority_order = {"high": 0, "medium": 1, "low": 2}
    messages.sort(key=lambda m: (m.get("read", False), priority_order.get(m.get("priority", "medium"), 1), m.get("timestamp", "")))
    
    # Save updated messages
    save_messages(to_agent, messages)
    
    # Return confirmation
    return [types.TextContent(
        type="text",
        text=f"✉️ Message from {from_agent} → {to_agent} (priority: {priority}){sender_warning}\n\nMessage preview:\n{message_text[:200]}{'...' if len(message_text) > 200 else ''}"
    )]

async def read_messages(args: Dict[str, Any]) -> list[types.TextContent]:
    """Read messages for the specified agent"""
    agent_name = args["agent_name"]
    mark_as_read = args.get("mark_as_read", True)
    priority_filter = args.get("priority_filter")
    include_read = args.get("include_read", False)
    
    # Validate agent identity for consistency
    available_agents = get_available_agents()
    agent_names = set(available_agents.keys())
    if agent_name not in agent_names:
        # Provide helpful guidance
        warning = [f"⚠️  Agent '{agent_name}' not recognized.\n"]
        warning.append(f"\nℹ️  To maintain consistent identity:\n")
        warning.append(f"   1. Use the same agent name when sending and reading messages\n")
        warning.append(f"   2. Choose from these known agents:\n")
        for name in sorted(agent_names):
            info = available_agents[name]
            warning.append(f"      • {name} - {info['description'][:50]}...\n")
        warning.append(f"\n💡 Tip: If you're a new agent, use a consistent identifier like 'feature-builder' or 'bug-fixer'\n")
        warning.append(f"\nChecking messages anyway for '{agent_name}'...\n\n")
        
        # Still try to load messages but include warning
        messages = load_messages(agent_name)
        if not messages:
            return [types.TextContent(
                type="text",
                text="".join(warning) + f"📭 No messages found for '{agent_name}'"
            )]
        # Continue with warning prefix
        warning_text = "".join(warning)
    else:
        warning_text = ""
        messages = load_messages(agent_name)
    
    if not messages:
        return [types.TextContent(
            type="text",
            text=warning_text + f"📭 No messages for {agent_name}"
        )]
    
    # Filter messages
    filtered = messages.copy()
    
    # Filter by read status
    if not include_read:
        filtered = [m for m in filtered if not m.get("read", False)]
    
    # Filter by priority
    if priority_filter:
        filtered = [m for m in filtered if m.get("priority") == priority_filter]
    
    # Mark as read if requested
    if mark_as_read:
        for msg in messages:
            if msg["id"] in [m["id"] for m in filtered]:
                msg["read"] = True
        save_messages(agent_name, messages)
    
    # Format response
    if not filtered:
        return [types.TextContent(
            type="text",
            text=warning_text + f"📭 No {'unread ' if not include_read else ''}messages{f' with priority {priority_filter}' if priority_filter else ''} for {agent_name}"
        )]
    
    # Build formatted output
    output = [f"📬 Messages for {agent_name} ({len(filtered)} message{'s' if len(filtered) != 1 else ''})\n"]
    output.append("=" * 60 + "\n")
    
    for msg in filtered:
        status = "✓" if msg.get("read") else "•"
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(msg.get("priority", "medium"), "⚪")
        
        output.append(f"\n{status} {priority_emoji} From: {msg.get('from', 'unknown')}")
        output.append(f"   Time: {msg.get('timestamp', 'unknown')}")
        output.append(f"   Priority: {msg.get('priority', 'medium').upper()}")
        
        if msg.get("context_files"):
            output.append(f"   Files: {', '.join(msg['context_files'])}")
        
        output.append(f"\n   Message:\n   {'-' * 50}")
        
        # Indent message content
        message_lines = msg.get("message", "").split('\n')
        for line in message_lines:
            output.append(f"   {line}")
        
        output.append(f"   {'-' * 50}\n")
    
    return [types.TextContent(
        type="text",
        text=warning_text + "\n".join(output)
    )]

async def clear_messages(args: Dict[str, Any]) -> list[types.TextContent]:
    """Archive old read messages"""
    agent_name = args["agent_name"]
    older_than_days = args.get("older_than_days", 7)
    
    # Validate agent for consistency
    available_agents = get_available_agents()
    agent_names = set(available_agents.keys())
    consistency_note = ""
    if agent_name not in agent_names:
        consistency_note = f"⚠️  Note: '{agent_name}' not in known agents. Ensure you use consistent naming.\n\n"
    
    # Load messages
    messages = load_messages(agent_name)
    
    if not messages:
        return [types.TextContent(
            type="text",
            text=consistency_note + f"📭 No messages to archive for {agent_name}"
        )]
    
    # Calculate cutoff time
    cutoff = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
    
    # Separate messages to keep and archive
    to_keep = []
    to_archive = []
    
    for msg in messages:
        # Parse timestamp
        try:
            msg_time = datetime.fromisoformat(msg.get("timestamp", "")).timestamp()
        except:
            msg_time = datetime.now().timestamp()
        
        # Check if should archive (read and old)
        if msg.get("read", False) and msg_time < cutoff:
            to_archive.append(msg)
        else:
            to_keep.append(msg)
    
    # Archive old messages if any
    if to_archive:
        archive_file = Path(MESSAGES_DIR) / "archive" / f"{agent_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        # Load existing archive if it exists
        existing_archive = []
        if archive_file.exists():
            try:
                with open(archive_file, 'r') as f:
                    existing_archive = json.load(f)
            except:
                pass
        
        # Append to archive
        existing_archive.extend(to_archive)
        
        # Save archive
        with open(archive_file, 'w') as f:
            json.dump(existing_archive, f, indent=2, default=str)
    
    # Save remaining messages
    save_messages(agent_name, to_keep)
    
    return [types.TextContent(
        type="text",
        text=consistency_note + f"🗄️ Archived {len(to_archive)} message{'s' if len(to_archive) != 1 else ''} for {agent_name}\n"
             f"📬 {len(to_keep)} message{'s' if len(to_keep) != 1 else ''} remaining"
    )]

async def list_agents(args: Dict[str, Any]) -> list[types.TextContent]:
    """List all available agents that can send/receive messages"""
    available_agents = get_available_agents()
    
    # Group agents by type/role if possible
    core_agent_names = ["memory-manager"]
    core_agents = {name: info for name, info in available_agents.items() if name in core_agent_names}
    project_agents = {name: info for name, info in available_agents.items() if name not in core_agent_names}
    
    output = ["📚 Available Agents for Messaging\n"]
    output.append("=" * 60 + "\n")
    
    if core_agents:
        output.append("\n🔧 Core Agents:\n")
        for name, info in sorted(core_agents.items()):
            output.append(f"\n   📦 {name}\n")
            output.append(f"      {info['description']}\n")
    
    if project_agents:
        output.append("\n📁 Project Agents:\n")
        for name, info in sorted(project_agents.items()):
            output.append(f"\n   📦 {name}\n")
            output.append(f"      {info['description']}\n")
    
    output.append("\n💡 Usage Tips:\n")
    output.append("   • Use consistent agent names across sessions\n")
    output.append("   • Check messages at session start: read_messages(agent_name=\"your-name\")\n")
    output.append("   • Send updates to relevant agents: create_message(from_agent=\"your-name\", to_agent=\"target\", ...)\n")
    
    return [types.TextContent(
        type="text",
        text="".join(output)
    )]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())