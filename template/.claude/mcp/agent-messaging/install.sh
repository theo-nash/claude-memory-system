#!/bin/bash
# Installation script for Agent Messaging MCP Server

set -e

echo "🚀 Installing Agent Messaging MCP Server..."

# Check if we're in the right directory
if [[ ! -f "server.py" ]]; then
    echo "❌ Error: Must run from .claude/mcp/agent-messaging/ directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make server executable
chmod +x server.py

# Create messages directory structure
MESSAGES_DIR="../../messages"
echo "📁 Creating messages directory structure..."
mkdir -p "$MESSAGES_DIR/archive"

# Create a simple test script
cat > test_server.py << 'EOF'
#!/usr/bin/env python3
"""Test script for Agent Messaging MCP Server"""

import json
import sys
import asyncio

async def test_server():
    print("🧪 Testing MCP server tools...")
    
    # This would normally connect to the server
    # For now, we just verify the server can be imported
    try:
        import server
        print("✅ Server module loads successfully")
        
        # Test that tools are defined (list_tools is an async function)
        app = server.app
        list_tools_handler = app.list_tools()
        tools = await list_tools_handler()  # Call the handler
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
EOF

chmod +x test_server.py

# Run test
echo "🧪 Running tests..."
python test_server.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use this MCP server, add the following to your Claude Code settings:"
echo ""
echo '  "mcpServers": {'
echo '    "agent-messaging": {'
echo '      "command": "python",'
echo '      "args": ["'$(pwd)'/server.py"],'
echo '      "env": {'
echo '        "MESSAGES_DIR": "'$(pwd)'/../../messages"'
echo '      }'
echo '    }'
echo '  }'
echo ""
echo "Or for global installation, use absolute paths."