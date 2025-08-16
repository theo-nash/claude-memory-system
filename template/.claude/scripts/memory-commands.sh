#!/bin/bash
# Claude Memory Management Commands
# Comprehensive utilities for memory system maintenance

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Detect Claude directory
detect_claude_dir() {
    if [[ -f ".claude/agents/memory-manager.md" ]]; then
        export CLAUDE_DIR=".claude"
    elif [[ -f "$HOME/.claude/agents/memory-manager.md" ]]; then
        export CLAUDE_DIR="$HOME/.claude"
    else
        echo -e "${RED}❌ Memory system not found${NC}"
        exit 1
    fi
}

# ====================
# CLEANUP & RESET COMMANDS
# ====================

memory_clean_cache() {
    echo -e "${BLUE}🧹 Cleaning cache files...${NC}"
    detect_claude_dir
    
    local cache_dir="$CLAUDE_DIR/cache"
    if [[ ! -d "$cache_dir" ]]; then
        echo "No cache directory found"
        return 0
    fi
    
    local count=$(find "$cache_dir" -name "*.md" 2>/dev/null | wc -l)
    if [[ $count -eq 0 ]]; then
        echo "Cache already clean"
        return 0
    fi
    
    echo "Found $count cache files"
    read -p "Delete all cache files? (y/N): " confirm
    
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        rm -f "$cache_dir"/*.md
        echo -e "${GREEN}✅ Removed $count cache files${NC}"
    else
        echo "Cancelled"
    fi
}

memory_reset() {
    local agent_name="$1"
    
    if [[ -z "$agent_name" ]]; then
        echo -e "${RED}❌ Usage: memory-reset <agent-name>${NC}"
        exit 1
    fi
    
    detect_claude_dir
    local agent_dir="$CLAUDE_DIR/memory/agents/$agent_name"
    
    if [[ ! -d "$agent_dir" ]]; then
        echo -e "${RED}❌ Agent '$agent_name' not found${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}⚠️  Resetting $agent_name memory (preserving TRDs)${NC}"
    echo "This will reset all memory files to initial state"
    read -p "Continue? (y/N): " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Cancelled"
        exit 0
    fi
    
    # Reset each memory file to placeholder content (simplified 4-file structure)
    cat > "$agent_dir/work-history.md" << EOF
# $agent_name: Work History

## Recent Completed Work
*No completed tasks yet*

<!-- Format: 
- **YYYY-MM-DD**: Brief task description - outcome/deliverable (TRD: filename)
-->
EOF

    cat > "$agent_dir/current-focus.md" << EOF
# $agent_name: Current Focus

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
EOF

    cat > "$agent_dir/expertise.md" << EOF
# $agent_name: Expertise

## Domain Knowledge
*No domain expertise documented yet*

## Technical Skills
*No technical skills recorded yet*

## Specialized Areas
*No specializations defined yet*
EOF

    cat > "$agent_dir/lessons.md" << EOF
# $agent_name: Lessons

## What Works Well
*No successful patterns documented yet*

## What to Avoid
*No pitfalls documented yet*

## Key Insights
*No insights recorded yet*

## Best Practices
*No best practices established yet*
EOF

    # Count preserved TRDs
    local trd_count=0
    if [[ -d "$agent_dir/trds" ]]; then
        trd_count=$(find "$agent_dir/trds" -name "*.md" 2>/dev/null | wc -l)
    fi
    
    echo -e "${GREEN}✅ Reset $agent_name memory files${NC}"
    echo "   Preserved $trd_count TRDs for audit trail"
}

memory_reset_all() {
    detect_claude_dir
    
    local preserve_trds=false
    if [[ "$1" == "--preserve-trds" ]]; then
        preserve_trds=true
    fi
    
    echo -e "${RED}⚠️  FULL MEMORY RESET${NC}"
    if $preserve_trds; then
        echo "Will preserve all TRDs"
    else
        echo "Will delete EVERYTHING including TRDs"
    fi
    
    echo "This affects ALL agents and team/project memories"
    read -p "Are you sure? Type 'reset-all' to confirm: " confirm
    
    if [[ "$confirm" != "reset-all" ]]; then
        echo "Cancelled"
        exit 0
    fi
    
    # Reset all agent directories
    for agent_dir in "$CLAUDE_DIR/memory/agents"/*; do
        if [[ -d "$agent_dir" ]]; then
            agent_name=$(basename "$agent_dir")
            echo "Resetting $agent_name..."
            
            if $preserve_trds; then
                # Use memory_reset function for each agent
                memory_reset "$agent_name" <<< "y" > /dev/null 2>&1
            else
                # Complete removal and recreation
                rm -rf "$agent_dir"
                mkdir -p "$agent_dir/trds"
                memory_reset "$agent_name" <<< "y" > /dev/null 2>&1
            fi
        fi
    done
    
    # Reset team files
    echo "Resetting team knowledge..."
    cat > "$CLAUDE_DIR/memory/team/shared-learnings.md" << 'EOF'
# Shared Learnings

## Cross-Agent Insights
*No shared learnings yet*
EOF

    cat > "$CLAUDE_DIR/memory/team/coordination-patterns.md" << 'EOF'
# Coordination Patterns

## Established Workflows
*No patterns documented yet*
EOF

    cat > "$CLAUDE_DIR/memory/team/handoff-protocols.md" << 'EOF'
# Handoff Protocols

## Standard Formats
*No protocols established yet*
EOF

    # Reset project files
    echo "Resetting project context..."
    cat > "$CLAUDE_DIR/memory/project/requirements.md" << 'EOF'
# Project Requirements

## Functional Requirements
*To be defined*

## Non-Functional Requirements
*To be defined*
EOF

    cat > "$CLAUDE_DIR/memory/project/architecture.md" << 'EOF'
# Architecture Decisions

## Design Patterns
*No patterns documented*

## Technology Stack
*To be defined*
EOF

    cat > "$CLAUDE_DIR/memory/project/constraints.md" << 'EOF'
# Project Constraints

## Technical Constraints
*No constraints documented*

## Business Constraints
*No constraints documented*
EOF

    cat > "$CLAUDE_DIR/memory/project/current-state.md" << 'EOF'
# Current Project State

## Completed Features
*None yet*

## In Progress
*None yet*

## Planned
*To be defined*
EOF

    # No separate handoffs to clear - coordination is in current-focus.md
    
    # Reset manager files
    echo "Resetting manager catalog..."
    cat > "$CLAUDE_DIR/memory/manager/document-catalog.md" << 'EOF'
# Document Catalog

## Agent TRDs
*No TRDs documented yet*

## Team Knowledge
*No team documents yet*

## Project Context
*No project documents yet*
EOF

    echo -e "${GREEN}✅ Full memory reset complete${NC}"
    if $preserve_trds; then
        local trd_total=$(find "$CLAUDE_DIR/memory/agents" -path "*/trds/*.md" 2>/dev/null | wc -l)
        echo "   Preserved $trd_total total TRDs"
    fi
}

memory_archive() {
    local days="${1:-30}"
    
    detect_claude_dir
    echo -e "${BLUE}📦 Archiving TRDs older than $days days...${NC}"
    
    local archive_dir="$CLAUDE_DIR/memory/archive"
    mkdir -p "$archive_dir"
    
    local archived=0
    local cutoff_date=$(date -d "$days days ago" +%Y%m%d 2>/dev/null || date -v-${days}d +%Y%m%d)
    
    # Find and archive old TRDs
    for trd_file in $(find "$CLAUDE_DIR/memory/agents" -path "*/trds/*.md" -type f 2>/dev/null); do
        # Extract date from filename (trd-YYYY-MM-DD-*)
        if [[ $(basename "$trd_file") =~ trd-([0-9]{4})-([0-9]{2})-([0-9]{2}) ]]; then
            file_date="${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}"
            
            if [[ "$file_date" < "$cutoff_date" ]]; then
                agent_name=$(basename $(dirname $(dirname "$trd_file")))
                
                # Create agent archive directory
                agent_archive="$archive_dir/$agent_name"
                mkdir -p "$agent_archive"
                
                # Move the file
                mv "$trd_file" "$agent_archive/"
                ((archived++))
            fi
        fi
    done
    
    if [[ $archived -eq 0 ]]; then
        echo "No TRDs older than $days days found"
    else
        echo -e "${GREEN}✅ Archived $archived TRDs${NC}"
        echo "   Location: $archive_dir"
    fi
}

# ====================
# KNOWLEDGE MANAGEMENT COMMANDS
# ====================

memory_seed() {
    local agent_name="$1"
    local knowledge="$2"
    
    if [[ -z "$agent_name" || -z "$knowledge" ]]; then
        echo -e "${RED}❌ Usage: memory-seed <agent-name> \"initial knowledge\"${NC}"
        exit 1
    fi
    
    detect_claude_dir
    local agent_dir="$CLAUDE_DIR/memory/agents/$agent_name"
    
    if [[ ! -d "$agent_dir" ]]; then
        echo "Creating agent directory for $agent_name..."
        mkdir -p "$agent_dir/trds"
        memory_reset "$agent_name" <<< "y" > /dev/null 2>&1
    fi
    
    echo -e "${BLUE}🌱 Seeding $agent_name with initial knowledge...${NC}"
    
    # Use memory-manager to process the seed knowledge
    cat << EOF > /tmp/seed_prompt.txt
Seed the $agent_name agent with the following initial knowledge:

$knowledge

Update their domain-knowledge.md, technical-knowledge.md, and best-practices.md files as appropriate based on this seed knowledge.
EOF

    # Call memory-manager via claude
    echo "Processing seed knowledge via memory-manager..."
    claude "$(cat /tmp/seed_prompt.txt)" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Direct seeding fallback${NC}"
        
        # Fallback: directly append to files
        echo -e "\n## Seeded Knowledge ($(date +%Y-%m-%d))\n$knowledge" >> "$agent_dir/domain-knowledge.md"
        echo -e "\n## Initial Expertise ($(date +%Y-%m-%d))\n$knowledge" >> "$agent_dir/technical-knowledge.md"
    }
    
    rm -f /tmp/seed_prompt.txt
    echo -e "${GREEN}✅ Seeded $agent_name with initial knowledge${NC}"
}

memory_learn() {
    local insight="$1"
    
    if [[ -z "$insight" ]]; then
        echo -e "${RED}❌ Usage: memory-learn \"global insight\"${NC}"
        exit 1
    fi
    
    detect_claude_dir
    local team_file="$CLAUDE_DIR/memory/team/shared-learnings.md"
    
    echo -e "${BLUE}💡 Adding team insight...${NC}"
    
    # Append to shared learnings
    cat << EOF >> "$team_file"

## Manual Insight ($(date +%Y-%m-%d))
- **Observation**: $insight
- **Source**: Manual entry via memory-learn command
- **Applicability**: All agents
EOF

    echo -e "${GREEN}✅ Added insight to team shared learnings${NC}"
}

memory_project() {
    local update="$1"
    
    if [[ -z "$update" ]]; then
        echo -e "${RED}❌ Usage: memory-project \"project update\"${NC}"
        exit 1
    fi
    
    detect_claude_dir
    echo -e "${BLUE}📋 Updating project context...${NC}"
    
    # Use memory-manager to process the update
    cat << EOF > /tmp/project_prompt.txt
Update the project memory files with the following information:

$update

Determine which project files need updating (requirements.md, architecture.md, constraints.md, or current-state.md) and update them appropriately.
EOF

    # Call memory-manager
    echo "Processing project update via memory-manager..."
    claude "$(cat /tmp/project_prompt.txt)" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Direct update fallback${NC}"
        
        # Fallback: append to current-state
        echo -e "\n## Update ($(date +%Y-%m-%d))\n$update" >> "$CLAUDE_DIR/memory/project/current-state.md"
    }
    
    rm -f /tmp/project_prompt.txt
    echo -e "${GREEN}✅ Updated project context${NC}"
}

memory_compact() {
    detect_claude_dir
    echo -e "${BLUE}🗜️  Compacting memory files...${NC}"
    
    local total_before=0
    local total_after=0
    
    # Process each agent's memory files
    for agent_dir in "$CLAUDE_DIR/memory/agents"/*; do
        if [[ ! -d "$agent_dir" ]]; then
            continue
        fi
        
        agent_name=$(basename "$agent_dir")
        echo "Processing $agent_name..."
        
        # Compact work-history.md - keep only last 20 entries
        if [[ -f "$agent_dir/work-history.md" ]]; then
            local before=$(wc -l < "$agent_dir/work-history.md")
            total_before=$((total_before + before))
            
            # Keep header and last 20 work entries
            head -n 3 "$agent_dir/work-history.md" > "$agent_dir/work-history.tmp"
            grep "^- \*\*20" "$agent_dir/work-history.md" | tail -20 >> "$agent_dir/work-history.tmp"
            echo "" >> "$agent_dir/work-history.tmp"
            echo "<!-- Older entries archived on $(date +%Y-%m-%d) -->" >> "$agent_dir/work-history.tmp"
            
            mv "$agent_dir/work-history.tmp" "$agent_dir/work-history.md"
            
            local after=$(wc -l < "$agent_dir/work-history.md")
            total_after=$((total_after + after))
        fi
        
        # Remove duplicate entries in lessons-learned.md
        for file in lessons-learned.md best-practices.md pitfalls-to-avoid.md; do
            if [[ -f "$agent_dir/$file" ]]; then
                local before=$(wc -l < "$agent_dir/$file")
                total_before=$((total_before + before))
                
                # Remove duplicate lines while preserving order and structure
                awk '!seen[$0]++ || /^#/ || /^$/' "$agent_dir/$file" > "$agent_dir/$file.tmp"
                mv "$agent_dir/$file.tmp" "$agent_dir/$file"
                
                local after=$(wc -l < "$agent_dir/$file")
                total_after=$((total_after + after))
            fi
        done
    done
    
    # Compact team shared-learnings - remove duplicates
    if [[ -f "$CLAUDE_DIR/memory/team/shared-learnings.md" ]]; then
        awk '!seen[$0]++ || /^#/ || /^$/' "$CLAUDE_DIR/memory/team/shared-learnings.md" > "$CLAUDE_DIR/memory/team/shared-learnings.tmp"
        mv "$CLAUDE_DIR/memory/team/shared-learnings.tmp" "$CLAUDE_DIR/memory/team/shared-learnings.md"
    fi
    
    local reduction=$((total_before - total_after))
    local percent=0
    if [[ $total_before -gt 0 ]]; then
        percent=$((reduction * 100 / total_before))
    fi
    
    echo -e "${GREEN}✅ Compaction complete${NC}"
    echo "   Lines before: $total_before"
    echo "   Lines after: $total_after"
    echo "   Reduction: $reduction lines ($percent%)"
}

# ====================
# MAIN COMMAND ROUTER
# ====================

show_help() {
    echo "Claude Memory Management Commands"
    echo "================================="
    echo ""
    echo "Cleanup & Reset:"
    echo "  memory-clean-cache           Remove all cache files"
    echo "  memory-reset <agent>         Reset specific agent (preserves TRDs)"
    echo "  memory-reset-all [--preserve-trds]  Reset all memories"
    echo "  memory-archive [days]        Archive TRDs older than X days (default: 30)"
    echo ""
    echo "Knowledge Management:"
    echo "  memory-seed <agent> \"text\"   Pre-populate agent knowledge"
    echo "  memory-learn \"insight\"       Add team-wide insight"
    echo "  memory-project \"update\"      Update project context"
    echo "  memory-compact               Consolidate and deduplicate memories"
    echo ""
    echo "Examples:"
    echo "  memory-reset task-executor"
    echo "  memory-seed api-specialist \"Expert in REST APIs and GraphQL\""
    echo "  memory-learn \"File operations are 30% faster with batch processing\""
    echo "  memory-archive 60"
}

# Parse command
case "$1" in
    "clean-cache")
        memory_clean_cache
        ;;
    "reset")
        memory_reset "$2"
        ;;
    "reset-all")
        memory_reset_all "$2"
        ;;
    "archive")
        memory_archive "$2"
        ;;
    "seed")
        memory_seed "$2" "$3"
        ;;
    "learn")
        memory_learn "$2"
        ;;
    "project")
        memory_project "$2"
        ;;
    "compact")
        memory_compact
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use 'memory-commands.sh help' for usage"
        exit 1
        ;;
esac