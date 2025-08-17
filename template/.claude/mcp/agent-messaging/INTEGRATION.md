# Agent Messaging MCP Server - Integration Guide

This guide explains how to integrate the agent messaging system into your Claude Code memory system.

## Quick Setup

1. **Install the MCP server:**
```bash
cd .claude/mcp/agent-messaging
chmod +x install.sh
./install.sh
```

2. **Add to Claude Code settings:**

Edit `.claude/settings.local.json` (for project) or `~/.claude/settings.json` (for global):

```json
{
  "mcpServers": {
    "agent-messaging": {
      "command": "python",
      "args": [".claude/mcp/agent-messaging/server.py"],
      "env": {
        "MESSAGES_DIR": ".claude/messages"
      }
    }
  }
}
```

3. **Restart Claude Code** to load the MCP server

## Agent Instructions Update

Add this section to each agent's instructions (in `.claude/agents/{agent-name}.md`):

```markdown
## Inter-Agent Messaging

You have access to MCP tools for direct communication with other agents.

### At Task Start
Always check for messages from other agents first:
- Use tool: `mcp__agent-messaging__read_messages`

Review any HIGH priority messages as they may contain critical information for your task.

### During Work
When you discover information specific to another agent:
- Use tool: `mcp__agent-messaging__create_message`
  - to_agent: Target agent name (e.g., "sdk-designer")
  - message: Specific information with examples/code
  - priority: "high" for critical, "medium" for useful, "low" for FYI
  - context_files: List of files they should review

### Examples

Reading messages:
```json
{
  "mark_as_read": true,
  "priority_filter": "high"
}
```

Sending a message:
```json
{
  "to_agent": "test-writer",
  "message": "Found security issue in auth module - needs immediate test coverage",
  "priority": "high",
  "context_files": ["/security/auth-vulnerability.md"]
}
```
```

## Memory System Integration

The messaging system complements the memory system:

### Memory System (via TRDs)
- Long-term knowledge and patterns
- General learnings applicable over time
- Project-wide insights
- Historical record

### Messaging System (via MCP)
- Real-time, specific information
- Targeted agent-to-agent communication
- Immediate action items
- Temporal coordination

## Testing

1. **Run tests:**
```bash
cd .claude/mcp/agent-messaging
source venv/bin/activate
python test_messaging.py
```

2. **Run demo:**
```bash
python demo.py
```

## Troubleshooting

### MCP Server Not Available

If agents can't access messaging tools:

1. Check server is in settings:
```bash
cat .claude/settings.local.json | grep agent-messaging
```

2. Verify server can start:
```bash
cd .claude/mcp/agent-messaging
source venv/bin/activate
python server.py
# Should see: "Ready to handle requests"
# Press Ctrl+C to stop
```

3. Restart Claude Code after settings changes

### Messages Not Appearing

1. Check messages directory exists:
```bash
ls -la .claude/messages/
```

2. Verify agent names match exactly:
```bash
ls .claude/agents/  # Note exact agent names
```

3. Check message files:
```bash
cat .claude/messages/{agent-name}.json
```

### Agent Name Detection

The server tries to detect the current agent from context. If this fails:

1. Messages will show "from: unknown"
2. Reading messages may fail
3. Solution: Ensure agents are invoked through standard Claude Code Task tool

## Architecture Notes

### File Structure
```
.claude/
├── mcp/
│   └── agent-messaging/     # MCP server code
│       ├── server.py         # Main server
│       ├── requirements.txt  # Dependencies
│       └── venv/            # Virtual environment
├── messages/                # Message storage
│   ├── sdk-designer.json   # Messages for sdk-designer
│   ├── test-writer.json    # Messages for test-writer
│   └── archive/            # Old messages
└── agents/                 # Agent definitions
    └── *.md                # Include messaging instructions
```

### Message Lifecycle

1. **Creation**: Agent A calls `create_message` → JSON saved to recipient's file
2. **Delivery**: Agent B calls `read_messages` → Messages loaded and returned
3. **Acknowledgment**: Messages marked as "read" when retrieved
4. **Cleanup**: Old read messages archived with `clear_messages`

### Design Principles

- **Simplicity**: One file per agent, JSON format
- **Explicit**: Agents consciously send/receive messages
- **Standalone**: Independent of memory system
- **Efficient**: Direct file I/O, no complex routing
- **Traceable**: All messages logged with timestamps

## Future Enhancements

Potential improvements (not in current version):

1. **Message Threading**: Reply to specific messages
2. **Broadcast Messages**: Send to multiple agents
3. **Priority Queue**: Auto-sort by priority and age
4. **Delivery Confirmation**: Track if message was read
5. **Message Templates**: Common message patterns
6. **Analytics**: Message flow visualization
7. **Web UI**: Monitor messages in browser

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Run the test suite to verify installation
3. Review demo.py for usage examples