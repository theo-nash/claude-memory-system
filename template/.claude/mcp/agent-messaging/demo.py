#!/usr/bin/env python3
"""
Demo script showing how agents would use the messaging system
Simulates a realistic workflow between multiple agents
"""

import os
import sys
import asyncio
from datetime import datetime

# Add server to path
sys.path.insert(0, os.path.dirname(__file__))

# Set up test environment - use absolute path for demo
import tempfile
demo_dir = tempfile.mkdtemp(prefix="msg_demo_")
os.environ["MESSAGES_DIR"] = demo_dir
print(f"📁 Using demo directory: {demo_dir}")

async def demo_agent_workflow():
    """Demonstrate a typical agent workflow with messaging"""
    
    from server import create_message, read_messages, clear_messages
    
    print("=" * 60)
    print("🎭 Agent Messaging Demo")
    print("=" * 60)
    print()
    
    # Scenario: Contract analyzer discovers critical information
    print("📋 Scenario: Contract analysis → SDK design → Testing")
    print("-" * 60)
    print()
    
    # Step 1: Contract Analyzer works and discovers something
    print("1️⃣ CONTRACT-ANALYZER is analyzing smart contracts...")
    os.environ["CURRENT_AGENT"] = "contract-analyzer"
    
    # Simulate discovery
    print("   🔍 Discovered: Hook permission system uses bitmaps")
    
    # Send targeted messages
    result = await create_message({
        "to_agent": "sdk-designer",
        "message": """Critical discovery about hook permissions:

The Uniswap V4 hooks use a bitmap pattern for permissions:
- 0x0001 = BEFORE_SWAP_FLAG
- 0x0002 = AFTER_SWAP_FLAG  
- 0x0004 = BEFORE_ADD_LIQUIDITY_FLAG
- 0x0008 = AFTER_ADD_LIQUIDITY_FLAG

You'll need to implement a builder pattern for this. Consider:
```typescript
const permissions = new HookPermissionBuilder()
  .allowBeforeSwap()
  .allowAfterSwap()
  .build();
```

See my full analysis at: /analysis/hooks/permissions.md""",
        "priority": "high",
        "context_files": ["/analysis/hooks/permissions.md", "/contracts/BaseHook.sol"]
    })
    print(f"   {result[0].text.split('Message:')[0]}")
    
    result = await create_message({
        "to_agent": "test-writer",
        "message": """Need test coverage for hook permissions:

Valid combinations to test:
- 0x0000 (no permissions)
- 0x0001 (only beforeSwap)
- 0x0003 (beforeSwap + afterSwap)
- 0x000F (all permissions)

Invalid combinations (should revert):
- 0x0010 (undefined bit)
- 0x0100 (reserved bit)

Test data available at: /analysis/hooks/test-cases.json""",
        "priority": "medium"
    })
    print(f"   {result[0].text.split('Message:')[0]}")
    print()
    
    # Step 2: SDK Designer starts work
    print("2️⃣ SDK-DESIGNER starting SDK implementation...")
    os.environ["CURRENT_AGENT"] = "sdk-designer"
    
    # Check messages
    print("   📬 Checking messages...")
    messages = await read_messages({"mark_as_read": True})
    
    # Extract key info from messages
    if "1 message" in messages[0].text:
        print("   ✉️ Received 1 message from contract-analyzer (HIGH priority)")
    else:
        print("   ✉️ Received message from contract-analyzer")
    
    print("   💡 Using bitmap pattern for permission builder as suggested")
    print("   🔨 Implementing HookPermissionBuilder class...")
    print()
    
    # SDK designer completes work and messages test-writer
    result = await create_message({
        "to_agent": "test-writer",
        "message": """SDK implementation ready for testing:

Created HookPermissionBuilder class at: /sdk/builders/HookPermissionBuilder.ts

Key methods to test:
- allowBeforeSwap()
- allowAfterSwap()
- allowBeforeAddLiquidity()
- allowAfterAddLiquidity()
- build() returns uint256

The builder validates against invalid bits and throws appropriate errors.
Please ensure your tests cover the edge cases mentioned by contract-analyzer.""",
        "priority": "high",
        "context_files": ["/sdk/builders/HookPermissionBuilder.ts"]
    })
    print(f"   {result[0].text.split('Message:')[0]}")
    print()
    
    # Step 3: Test Writer receives multiple messages
    print("3️⃣ TEST-WRITER preparing test suite...")
    os.environ["CURRENT_AGENT"] = "test-writer"
    
    # Check messages
    print("   📬 Checking messages...")
    messages = await read_messages({"include_read": False})
    
    # Count messages
    if "2 messages" in messages[0].text:
        print("   ✉️ Received 2 messages:")
        print("      - contract-analyzer: Test cases for permissions (MEDIUM)")
        print("      - sdk-designer: SDK ready for testing (HIGH)")
    
    print("   🧪 Creating comprehensive test suite...")
    print("   ✅ Tests cover both valid and invalid permission combinations")
    print("   ✅ Tests verify builder pattern implementation")
    print()
    
    # Step 4: Show message summary
    print("=" * 60)
    print("📊 Message Flow Summary:")
    print("-" * 60)
    print("contract-analyzer → sdk-designer: Hook permission discovery")
    print("contract-analyzer → test-writer: Test case requirements")
    print("sdk-designer → test-writer: SDK implementation ready")
    print()
    print("✨ All agents coordinated through direct messaging!")
    print("=" * 60)

async def main():
    """Run the demo"""
    try:
        await demo_agent_workflow()
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())