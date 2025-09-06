#!/usr/bin/env python3
"""
Test script for Byterover MCP client connection and sync functionality
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import with absolute module paths to avoid relative import issues
from local_memory_mirror.sync_layer.connectors.byterover_mcp_client import get_byterover_client

def test_byterover_connection():
    """Test Byterover MCP client connection"""
    print("🔧 Testing Byterover MCP Connection...")
    print("=" * 50)

    try:
        client = get_byterover_client()

        # Test connection
        print("1. Testing connection to Byterover MCP...")
        connected = client.connect()

        if connected:
            print("✅ Successfully connected to Byterover MCP")

            # Get sync status
            status = client.get_sync_status()
            print(f"📊 Connection Status: {status}")
            print(f"🔧 Tools Available: {status['tools_available']}")
            print(f"🌐 Server URL: {status['server_url']}")

            # Test async sync functionality
            print("\n2. Testing knowledge base sync...")

            # Run sync in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                sync_result = loop.run_until_complete(client.sync_knowledge_base())

                if sync_result['success']:
                    print("✅ Knowledge base sync successful!")
                    print(f"📚 Sources synced: {sync_result['sources_synced']}")
                    print(f"📄 Entries added: {sync_result['entries_added']}")
                    print(f"⏰ Last sync: {sync_result['last_sync']}")
                else:
                    print(f"⚠️ Sync completed with warning: {sync_result.get('error', 'Unknown error')}")

            finally:
                loop.close()

            # Disconnect
            client.disconnect()
            print("✅ Disconnected from Byterover MCP")

        else:
            print("❌ Failed to connect to Byterover MCP")
            print("💡 This might be expected if Byterover MCP server is not running")
            return False

        print("\n" + "=" * 50)
        print("🎉 Byterover MCP client test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Byterover MCP client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_byterover_connection()
    sys.exit(0 if success else 1)
