# Claude Code Subagent Memory System

**Persistent memory and learning for Claude Code subagents - smart agents that never lose context**

[![npm version](https://img.shields.io/npm/v/claude-subagent-memory.svg)](https://www.npmjs.com/package/claude-subagent-memory)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Install

```bash
npx claude-subagent-memory
```

One command gives your Claude Code subagents persistent memory and adaptive learning across sessions.

## 🎯 The Problem

**Claude Code subagents have no memory between sessions.** Every time you invoke a subagent like `task-executor` or your custom agents, they start completely fresh with:

- ❌ No memory of previous tasks completed
- ❌ No lessons learned from past mistakes
- ❌ No awareness of project architecture
- ❌ No knowledge of what other subagents discovered
- ❌ No context from earlier work

**Result:** Your subagents repeatedly make the same mistakes, rediscover the same patterns, and waste tokens getting re-explained the same context every single time.

## ✨ The Solution

This system provides **automatic persistent memory** for all your Claude Code subagents through:

- 📝 **Task Reflection Documents (TRDs)** - Subagents document their learnings
- 🧠 **Memory-Manager Subagent** - Intelligently coordinates knowledge
- 🔄 **Automatic Hooks** - Context loads when subagents start, saves when they finish
- 📚 **Structured Memory Files** - Organized, searchable knowledge base
- ⚡ **Slash Commands** - Easy memory operations in Claude Code

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
│   ├── add_trd_protocol.py    # SessionStart: Adds TRD protocol to subagents
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

### Automatic Workflow
1. **You invoke a subagent** → `Use task-executor to implement feature X`
2. **PreToolUse hook fires** → Loads relevant context via memory-manager
3. **Subagent works** → Has full awareness of past work and lessons
4. **Subagent creates TRD** → Documents discoveries before completing
5. **SubagentStop hook fires** → Processes TRD, updates memories
6. **Knowledge saved** → Available for all future subagent sessions

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
npx claude-subagent-memory
```

### Option 2: Clone Repository
```bash
git clone https://github.com/yourusername/claude-subagent-memory.git
cd claude-subagent-memory
npm run setup
```

### Option 3: Manual Setup
Copy the `template/` directory to your `.claude/` folder and run:
```bash
chmod +x .claude/scripts/*
chmod +x .claude/hooks/*.py
```

## 💡 Key Features

- **Zero Configuration** - Works out of the box
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

**Transform your Claude Code subagents from stateless workers into a continuously learning team!**

*If this helps your subagents remember, please ⭐ the repo!*