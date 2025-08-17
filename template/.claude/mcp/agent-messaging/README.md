# Agent Messaging MCP Server

Direct agent-to-agent communication system for Claude Code subagents with enhanced identity management and discovery.

## Overview

This MCP (Model Context Protocol) server enables agents to send messages directly to each other, separate from the persistent memory system. Messages are delivered through a simple inbox system where agents can check for updates from other agents.

## Key Features

- **Direct Messaging**: Send targeted messages to specific agents
- **Agent Discovery**: Dynamically discovers available agents from `.claude/agents/`
- **Explicit Identity**: All operations require explicit agent identification
- **Priority Levels**: High, medium, low priority messages
- **Message Persistence**: Messages saved until read and archived
- **Smart Error Recovery**: Helpful guidance with full agent list when names are incorrect
- **Context Files**: Attach file references for recipient review

## Installation

The MCP server is automatically set up during the memory system installation:

1. Python virtual environment created in `venv/`
2. Dependencies installed from `requirements.txt`
3. Server configured in `.claude/.mcp.json` (project) or `settings.json` (global)

### Manual Setup

If needed, from `.claude/mcp/agent-messaging/`:

```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Tools

### 1. `list_agents`
Discover all available agents you can message, with their descriptions.

**Parameters:** None

**Returns:** List of agents with their descriptions, grouped by type

**Example:**
```python
list_agents()

# Example output:
# 📚 Available Agents for Messaging
# ========================================
# 
# 🔧 Core Agents:
# 
#    📦 memory-manager
#       Lightweight memory coordinator for Claude Code subagents...
# 
# 📁 Project Agents:
# 
#    📦 api-designer
#       Expert in RESTful API design, OpenAPI specifications...
#    
#    📦 test-writer
#       Creates comprehensive test suites including unit, integration...
```

### 2. `create_message`
Send a message to another agent.

**Parameters:**
- `from_agent` (string, required): Your agent name (sender)
- `to_agent` (string, required): Recipient agent name
- `message` (string, required): Message content
- `priority` (string): "high", "medium", or "low" (default: "medium")
- `context_files` (array): List of file paths to reference

**Example:**
```python
create_message(
    from_agent="api-designer",    # Required: Who you are
    to_agent="test-writer",        # Required: Who to send to
    message="New API endpoints added: /users, /products",
    priority="high",
    context_files=["api/users.py", "api/products.py"]
)
```

**Error Handling:**
If recipient doesn't exist, you'll receive:
- Complete list of available agents
- Suggestions for similar names
- Exact retry syntax

### 3. `read_messages`
Check your messages from other agents.

**Parameters:**
- `agent_name` (string, required): Your agent name (whose messages to read)
- `mark_as_read` (boolean): Mark messages as read (default: true)
- `priority_filter` (string): Filter by priority level
- `include_read` (boolean): Include already-read messages (default: false)

**Example:**
```python
read_messages(
    agent_name="test-writer",     # Required: Who you are
    mark_as_read=True,
    priority_filter="high"
)
```

### 4. `clear_messages`
Archive old read messages to keep inbox clean.

**Parameters:**
- `agent_name` (string, required): Your agent name
- `older_than_days` (integer): Archive messages older than N days (default: 7)

**Example:**
```python
clear_messages(
    agent_name="test-writer",
    older_than_days=7
)
```

## Usage Pattern

### Recommended Workflow

1. **Start of session**: Check who's available and read messages
```python
# See available agents
list_agents()

# Check your inbox (use YOUR agent name)
read_messages(agent_name="your-agent-name")
```

2. **During work**: Send updates to relevant agents
```python
create_message(
    from_agent="your-agent-name",
    to_agent="target-agent",
    message="Important update about...",
    priority="high"
)
```

3. **Maintain consistency**: Use the same agent name throughout
- When sending: `from_agent="feature-builder"`
- When reading: `agent_name="feature-builder"`
- When clearing: `agent_name="feature-builder"`

## Agent Identity System

### The Challenge
Subagents don't automatically know their own identity, requiring explicit identification.

### The Solution
- **Explicit Identity**: All operations require you to specify your agent name
- **Dynamic Discovery**: System finds all available agents from `.claude/agents/`
- **Consistency Enforcement**: Warnings when using unrecognized agent names
- **Helpful Recovery**: Full agent list and suggestions on errors

### Error Response Example
When you specify an unknown agent:
```
❌ Agent 'unknown-agent' not found.

💡 Did you mean one of these?
   • api-designer
   • api-specialist

📋 Available agents:
   • api-designer
   • database-expert
   • memory-manager
   • test-writer
   • ui-builder

🔄 Please retry with: create_message(from_agent="your-name", to_agent="<correct-agent-name>", ...)
```

## Agent Instructions Template

Add to your agent's instructions:

```markdown
## Inter-Agent Communication

You have access to MCP tools for messaging other agents.

### At session START:
1. Check available agents: list_agents()
2. Read your messages: read_messages(agent_name="YOUR-AGENT-NAME")

### During work:
When you discover something relevant for another agent:
- Use: create_message(
    from_agent="YOUR-AGENT-NAME",
    to_agent="target-agent",
    message="Specific information",
    priority="high"  # if urgent
  )

### Identity consistency:
ALWAYS use the same agent name for all operations in a session.
If unsure of your name, use a descriptive identifier like "feature-builder".
```

## Message Format

Messages are stored as JSON:
```json
{
  "id": "msg-20240101-120000-apidesig",
  "from": "api-designer",
  "to": "test-writer",
  "message": "New endpoints need testing",
  "priority": "high",
  "timestamp": "2024-01-01T12:00:00",
  "context_files": ["api/users.py"],
  "read": false
}
```

## File Structure

```
.claude/
├── mcp/
│   └── agent-messaging/
│       ├── server.py          # MCP server implementation
│       ├── requirements.txt   # Python dependencies
│       ├── README.md          # This file
│       └── venv/              # Python virtual environment
└── messages/                  # Message storage
    ├── {agent-name}.json      # Inbox for each agent
    └── archive/               # Archived messages
```

## Agent Discovery

The server discovers agents by:
1. Scanning `.claude/agents/` directories (project and global)
2. Parsing YAML frontmatter from each agent file
3. Extracting the actual agent name and description
4. Using the frontmatter `name:` field, not the filename

This means:
- Agent identity comes from the file content, not filename
- Descriptions are shown to help identify the right recipient
- The `list_agents` tool shows both name and description

## Best Practices

1. **Check messages at session start**: Always run `read_messages()` first
2. **Use consistent names**: Pick one name and stick with it throughout session
3. **Be descriptive**: If you don't know your agent name, use something descriptive
4. **Include context**: Reference specific files or code in messages
5. **Set appropriate priority**: 
   - "high" for blocking issues
   - "medium" for coordination
   - "low" for FYI
6. **Archive regularly**: Use `clear_messages()` to keep inbox manageable

## Troubleshooting

### "Agent not found" errors
- Run `list_agents()` to see available agents
- Check for typos in agent names
- Use the exact retry syntax provided in error message

### Messages not appearing
- Verify you're using the correct `agent_name` when reading
- Check that sender used correct `to_agent` name
- Ensure consistent identity across operations

### Identity confusion
- Pick ONE agent name per session
- Use same name for sending AND reading
- Consider adding your agent name to your instructions

### Python/MCP errors
- Ensure Python 3.8+ is installed
- Check virtual environment exists: `.claude/mcp/agent-messaging/venv/`
- Verify MCP configuration in `.claude/.mcp.json` or settings file

## Integration with Memory System

This messaging system complements the memory management system:

- **Memory System**: Long-term knowledge, learnings, and patterns
- **Messaging System**: Real-time, specific information sharing
- **TRDs**: Document significant discoveries for permanent storage
- **Messages**: Share immediate, actionable information

## Testing

Test the server functionality:
```bash
python test_messaging.py
```

Tests include:
- Agent discovery
- Message creation with identity
- Error handling for unknown agents
- Priority sorting
- Archive functionality