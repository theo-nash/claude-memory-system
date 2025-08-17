# Claude Code Subagent Memory System

**Zero-dependency persistent memory for Claude Code subagents - orchestrated through a specialized subagent and native hook mechanisms**

[![npm version](https://img.shields.io/npm/v/claude-subagent-memory.svg)](https://www.npmjs.com/package/claude-subagent-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

## 🚀 Quick Install

```bash
# Navigate to your project directory first!
cd your-project

# Then run the installer
npx claude-subagent-memory
```

This will install the memory system in your project's `.claude/` directory.

## 🎯 The Problem

**Claude Code subagents have no memory between sessions.** Every time you invoke a subagent like `task-executor` or your custom agents, they start completely fresh with:

- ❌ No memory of previous tasks completed
- ❌ No lessons learned from past mistakes
- ❌ No awareness of project architecture
- ❌ No knowledge of what other subagents discovered
- ❌ No context from earlier work

**Result:** Your subagents repeatedly make the same mistakes, rediscover the same patterns, and waste tokens getting re-explained the same context every single time.

## ✨ The Solution

This **zero-dependency** system orchestrates persistent memory through Claude Code's native capabilities:

- 🎯 **Centralized Orchestration** - A specialized `memory-manager` subagent coordinates all memory operations
- 🔄 **Native Hook Mechanisms** - Leverages Claude Code's built-in SessionStart, PreToolUse, and SubagentStop hooks
- 📝 **Task Reflection Documents (TRDs)** - Subagents self-document their learnings and discoveries
- 🚫 **No External Dependencies** - Purely uses Claude Code's native subagent and hook systems
- 📚 **Structured Memory Files** - Git-friendly markdown knowledge base
- ⚡ **Slash Commands** - Native Claude Code commands for memory operations

## 🆕 New: Agent-to-Agent Messaging

The system now includes an **MCP (Model Context Protocol) server** for direct agent-to-agent messaging:
- Agents can send targeted messages to specific other agents
- Messages are delivered through MCP tools (create_message, read_messages)
- Automatic setup during installation (requires Python 3.8+)
- Zero additional configuration needed

## 📦 What Gets Installed

```
.claude/
├── agents/
│   └── memory-manager.md       # Subagent that manages all memory operations
├── commands/                   # Slash commands for Claude Code interface
│   ├── memory-status.md       # /memory-status
│   ├── memory-load.md         # /memory-load <agent> "task"
│   ├── memory-search.md       # /memory-search "term"
│   └── ... (14 commands)
├── hooks/                      # Automation hooks (fire automatically)
│   ├── initialize_agent_system.py  # SessionStart: Complete agent initialization
│   ├── subagent_memory_analyzer.py  # SubagentStop: Processes completed work
│   └── context_cache_checker.py     # PreToolUse: Loads context for subagents
├── scripts/
│   ├── claude-memory          # Shell wrapper for memory-manager subagent
│   └── memory-commands.sh     # Maintenance utilities
└── memory/                    # Knowledge storage
    ├── agents/{name}/         # Per-subagent memories (4-file structure)
    │   ├── work-history.md    # What I've done
    │   ├── current-focus.md   # What I'm doing
    │   ├── expertise.md       # What I know
    │   ├── lessons.md         # What I've learned
    │   └── trds/             # Task Reflection Documents
    ├── team/                  # Cross-subagent knowledge
    ├── project/              # Project-wide context
    └── manager/              # Catalogs and coordination
```

## 🎮 How It Works

### Architecture: Zero-Dependency Orchestration
The system achieves persistent memory **without any external dependencies** by leveraging Claude Code's native subagent system. A specialized `memory-manager` subagent acts as the central coordinator, creating context caches that subagents can load directly - cleverly avoiding Claude Code's session-within-a-session constraints.

### Automatic Workflow
1. **You invoke a subagent** → `Use task-executor to implement feature X`
2. **PreToolUse hook fires** → Invokes `memory-manager` subagent to create a context cache file
3. **Cache created** → Memory-manager writes relevant context to `.claude/cache/task-{id}.md`
4. **Subagent prompted** → Hook instructs subagent to read the cache file directly
5. **Subagent works** → Has full awareness of past work and lessons from the cache
6. **Subagent creates TRD** → Documents discoveries before completing
7. **SubagentStop hook fires** → Invokes `memory-manager` to process TRD and update memories
8. **Knowledge saved** → Available for all future subagent sessions

### Manual Operations via Slash Commands

```bash
# Check what your subagents know
/memory-status

# Pre-load context for a specific task
/memory-load task-executor "implement OAuth2 authentication"

# Search across all subagent memories
/memory-search "error handling patterns"

# Add a team-wide insight
/memory-learn "Batch processing improves performance by 30%"

# See all available commands
/memory-help
```

## 🛠️ Subagent Integration

### For Existing Subagents
The system automatically adds TRD protocol to all your existing subagents when you restart Claude Code.

### For New Subagents
Create your subagent in `.claude/agents/` and the memory system automatically:
- Adds TRD protocol on next restart
- Creates memory structure on first use
- Manages context and knowledge persistence

### Example Subagent with Memory
```markdown
---
name: api-specialist
description: Expert in API design and implementation
---

[Your subagent instructions]

<!-- TRD Protocol automatically added by memory system -->
```

## 📊 Real-World Impact

### Before Memory System
```
Session 1: task-executor implements auth → discovers bcrypt is best
Session 2: task-executor implements auth → tries MD5, then discovers bcrypt
Session 3: task-executor implements auth → tries MD5, then discovers bcrypt
```

### After Memory System
```
Session 1: task-executor implements auth → discovers bcrypt, saves to memory
Session 2: task-executor implements auth → loads context, uses bcrypt immediately
Session 3: task-executor enhances auth → builds on previous implementation
```

## 🔧 Installation Options

### Option 1: NPX (Recommended)
```bash
cd your-project  # Important: Be in your project directory!
npx claude-subagent-memory
```

### Option 2: Clone Repository
```bash
cd your-project  # Navigate to your project first
git clone https://github.com/theo-nash/claude-memory-system.git /tmp/claude-memory-system
cd /tmp/claude-memory-system
npm install
node bin/install.js
```

### Option 3: Manual Setup
```bash
cd your-project  # Navigate to your project first
```
Copy the `template/` directory contents to your `.claude/` folder and run:
```bash
chmod +x .claude/scripts/*
chmod +x .claude/hooks/*.py
```

## 💡 Key Features

- **Zero Dependencies** - Pure Claude Code solution using native subagents and hooks
- **Centralized Orchestration** - Single `memory-manager` subagent coordinates all operations
- **Zero Configuration** - Works out of the box with Claude Code's built-in capabilities
- **Token Efficient** - Only loads relevant context (1500-3000 tokens)
- **Git Friendly** - All memories in readable markdown
- **Graceful Degradation** - Failures don't block subagent work
- **Knowledge Spreading** - Insights propagate based on significance
- **Search Capable** - Find knowledge across all subagent memories

## 📚 Documentation

After installation, full documentation is available at:
- `.claude/memory/README.md` - Complete system documentation
- `/memory-help` - Command reference in Claude Code

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT - See [LICENSE](LICENSE)

## 🙏 Credits

Built by the Claude Code community to solve the subagent memory problem.

---

## 🏗️ Why Zero Dependencies?

This system is built entirely on Claude Code's native capabilities:
- **Native Subagents** - The `memory-manager` is a standard Claude Code subagent
- **Native Hooks** - Uses Claude Code's built-in hook system for automation
- **Native Commands** - Slash commands are standard Claude Code commands
- **Native File Operations** - Uses only Read/Write/Edit tools available to all subagents
- **Cache-Based Architecture** - Avoids session-within-a-session constraints through file-based context passing

**Result:** No external packages, no version conflicts, no security vulnerabilities from third-party code. Just pure Claude Code orchestration that works within platform constraints.

---

**Transform your Claude Code subagents from stateless workers into a continuously learning team - with zero external dependencies!**

*If this helps your subagents remember, please ⭐ the repo!*