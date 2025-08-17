# Claude Code Memory Management System

**A zero-dependency, automated memory system that gives Claude Code subagents persistent knowledge across sessions.**

## 🚨 The Problem

Every time you launch a Claude Code subagent, it starts completely fresh with **zero memory** of:
- ❌ Previous work completed
- ❌ Lessons learned from mistakes  
- ❌ Project architecture and requirements
- ❌ What other agents are working on
- ❌ Technical knowledge discovered

**The Result?** Your agents repeatedly make the same mistakes, reinvent solutions, and waste tokens re-explaining context every single time.

## ✨ The Solution  

An **intelligent memory management system** that automatically:
- 📝 **Captures** insights from every subagent session
- 🧠 **Organizes** knowledge into structured memory files
- 🔄 **Provides** relevant context when agents start tasks
- 📈 **Spreads** important discoveries across your team
- 🎯 **Works silently** - no manual intervention needed

## 🚀 Quick Start

```bash
# Run the setup script
bash setup_memory_v3.sh

# Restart Claude Code to activate
# That's it! Memory system is now active
```

## 🔄 How It Works

### The Complete Workflow

1. **📢 You call a subagent** → PreToolUse hook detects this
2. **🧠 Context loads automatically** → Memory-manager provides relevant knowledge
3. **⚡ Agent works with full context** → No need to re-explain everything
4. **📝 Agent creates TRD** → Documents what it learned
5. **💾 Knowledge saved automatically** → SubagentStop hook processes insights
6. **🔄 Ready for next task** → Knowledge available for future work

### What Happens Behind the Scenes

```
Your Command: "Use task-executor to implement feature X"
                    ↓
    [PreToolUse Hook] → Loads context for task-executor
                    ↓
    [Task-Executor Works] → Has full project awareness
                    ↓
    [Creates TRD] → Documents discoveries and decisions
                    ↓
    [SubagentStop Hook] → Processes TRD via memory-manager
                    ↓
    [Knowledge Stored] → Available for all future tasks
```

## 📁 Memory Structure

Each agent maintains organized knowledge in a simple 4-file structure:

```
.claude/memory/agents/{agent-name}/
├── work-history.md      # What I've done (completed tasks)
├── current-focus.md     # What I'm doing (active work + coordination)
├── expertise.md         # What I know (technical knowledge)
├── lessons.md          # What I've learned (patterns & pitfalls)
└── trds/               # Task Reflection Documents (detailed logs)
```

Plus shared knowledge areas:

```
.claude/memory/
├── manager/            # Core catalogs and project overview
├── team/              # Cross-agent insights and patterns
└── project/           # Architecture, requirements, constraints
```

## 🧠 Memory Operations

### Slash Commands (Use in Claude Code)

The memory system provides slash commands you can use directly in Claude Code:

#### Core Operations
- `/memory-status` - Check system status and agent memories
- `/memory-load <agent> "task"` - Load context for an agent
- `/memory-update <agent> "insights"` - Store new insights
- `/memory-search "term"` - Search all memories for a topic

#### Maintenance Commands
- `/memory-clean` - Remove cache files
- `/memory-reset <agent>` - Reset specific agent memory
- `/memory-reset all` - Reset all memories (preserves TRDs)
- `/memory-archive [days]` - Archive old TRDs (default: 30 days)
- `/memory-compact` - Deduplicate and optimize memories

#### Knowledge Management
- `/memory-seed <agent> "knowledge"` - Pre-populate agent knowledge
- `/memory-learn "insight"` - Add team-wide learning
- `/memory-project "update"` - Update project context
- `/memory-process-trd <agent> <path>` - Manually process a TRD
- `/memory-help` - Show all available commands

### Command Examples

```bash
# Load context for a task
/memory-load task-executor "implement user authentication"

# Search for specific knowledge
/memory-search "API design patterns"

# Add team-wide insight
/memory-learn "Batch operations improve performance by 30%"

# Seed new agent with knowledge
/memory-seed api-specialist "Expert in REST APIs and GraphQL"

# Archive old TRDs (older than 60 days)
/memory-archive 60

# Reset a specific agent's memory
/memory-reset task-executor

# Update project requirements
/memory-project "Added requirement for OAuth2 support"
```

### Shell Wrapper (Alternative)

You can also use the `claude-memory` shell wrapper directly:

```bash
# Load context for an agent before a task
./claude-memory load-context agent-name "task description"

# Check system status
./claude-memory status
```

### Automatic Operations (No Action Needed!)

✅ **Context Loading** - Happens automatically when subagent starts  
✅ **TRD Processing** - Happens automatically when subagent completes  
✅ **Knowledge Spreading** - Based on significance levels:
  - **Routine** (70%) → Stays in agent's memory
  - **Notable** (25%) → Spreads to team knowledge
  - **Significant** (5%) → Updates project-wide

## 📝 Task Reflection Documents (TRDs)

Every agent creates a TRD before completing - it's their way of documenting what they learned:

```markdown
# What's in a TRD?
- What the agent accomplished
- Key discoveries and insights  
- Work ready for other agents
- Issues that need follow-up
- Knowledge for the team
- Project-level impacts
```

TRDs are processed automatically by the memory-manager based on their significance level.

## 🎯 Key Benefits

### Immediate Wins
- **No More Repetition** - Agents remember previous solutions
- **Faster Development** - Build on past discoveries
- **Better Coordination** - Agents know what others are doing
- **Token Efficiency** - Stop re-explaining context

### Long-term Value  
- **Continuous Learning** - Your team gets smarter over time
- **Institutional Knowledge** - Preserves project understanding
- **Best Practices** - Successful patterns propagate automatically
- **Reduced Errors** - Learn from mistakes once, not repeatedly

## 💡 Usage Examples

### Basic Workflow (Fully Automatic)
```bash
# Just use your subagents normally!
"Use task-executor to implement the login feature"

# Behind the scenes:
# 1. Context loads automatically
# 2. Agent works with full knowledge
# 3. Creates TRD when done
# 4. Memory updates automatically
```

### Using Slash Commands
```bash
# Load context before a task
/memory-load task-executor "implement OAuth2 login"

# Search for existing knowledge
/memory-search "authentication patterns"

# Add a discovery to team knowledge
/memory-learn "Redis caching reduced API latency by 40%"

# Check system status
/memory-status
```

### Managing Memories
```bash
# Reset an agent's memory (keeps TRDs)
/memory-reset api-specialist

# Archive old TRDs
/memory-archive 90

# Clean up cache files
/memory-clean

# Optimize memory files
/memory-compact
```

## 💰 Token Efficiency

The system is incredibly lightweight:
- **Smart Loading**: Only loads relevant knowledge (~1500-3000 tokens)
- **Catalog System**: Indexes knowledge for targeted retrieval
- **Auto Cleanup**: Removes temporary cache files after use
- **Net Positive**: Saves far more tokens than it uses by avoiding repetition

## 🔧 Troubleshooting

### Quick Fixes

**"Subagent didn't get context"**
```bash
# Check system status
claude-memory status

# Restart Claude Code
# Memory hooks will reload
```

**"Memory not updating"**
```bash
# Check debug logs
tail -f ~/.claude/subagentstop_debug.log

# Verify TRD was created
ls .claude/memory/agents/*/trds/
```

**"Command not found: claude-memory"**
```bash
# Make wrapper executable
chmod +x claude-memory

# Or use directly
./claude-memory status
```

## 🏗️ System Components

### Core Files
- **memory-manager.md** - The brain that coordinates all memory operations
- **claude-memory** - Shell wrapper for direct memory operations
- **14 Slash Commands** - Native Claude Code commands in `.claude/commands/`
- **3 Automated Hooks**:
  - `initialize_agent_system.py` - Complete agent initialization at session start
  - `subagent_memory_analyzer.py` - Processes insights when agents complete
  - `context_cache_checker.py` - Loads context when agents start

### Why This Architecture?

✅ **Zero Dependencies** - Uses only Claude Code's native tools  
✅ **Git-Friendly** - All memories in readable markdown files  
✅ **Graceful Degradation** - System failures don't block work  
✅ **Human-Readable** - You can review and edit memories manually  
✅ **Lightweight** - Minimal token overhead with maximum value

## 🎉 Results

After installation, your subagent team will have:
- **Persistent Learning** - Knowledge accumulates over time
- **Automatic Context** - Agents start with relevant knowledge
- **Team Coordination** - Agents aware of each other's work
- **Continuous Improvement** - Best practices spread automatically

**Transform your subagents from isolated workers into a continuously learning team!**

## 📚 Advanced Topics

### Creating New Agents
1. Add agent definition to `.claude/agents/`
2. TRD protocol adds automatically on restart
3. Memory scaffolding creates on first use

### Knowledge Spreading Rules
- **Agent → Team**: When insights apply to multiple agents
- **Team → Project**: When patterns become standards
- **Discovery → Global**: When constraints affect everything

### Manual TRD Creation
Agents should create TRDs automatically, but you can also create them manually in `.claude/memory/agents/{name}/trds/` following the standard format.

---

*Give your Claude Code subagents the memory they deserve - install the memory management system today!*