#!/usr/bin/env python3
"""
MCP Troubleshooting Guide and Test Suite

This script helps diagnose and fix MCP connectivity issues.
Use this to test MCP server connections and validate configurations.
"""

import json
import requests
import time
import uuid
import subprocess
from pathlib import Path

def check_mcp_server_status():
    """Check if the MCP server is running and responsive."""
    print("🔍 Checking MCP server status...")

    try:
        # Try a simple health check first
        health_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": "health_check",
            "method": "health_check",
            "params": {}
        }

        response = requests.post(
            "http://localhost:8051/mcp",
            json=payload,
            headers=health_headers,
            timeout=10
        )

        print(f"✅ MCP server responded: {response.status_code}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ MCP server not responding: {e}")
        return False

def test_mcp_configuration_compatibility():
    """Test MCP server with proper Cline-compatible configuration."""
    print("\n🔧 Testing MCP configuration compatibility...")

    session_id = str(uuid.uuid4())

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Session-ID": session_id,
        "User-Agent": "Cline/1.0.0"
    }

    # Step 1: Initialize session with Cline-compatible protocol
    init_payload = {
        "jsonrpc": "2.0",
        "id": "init_test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "Cline",
                "version": "3.x.x"
            }
        }
    }

    print("Step 1: Initializing MCP session with Cline-compatible headers...")

    try:
        response = requests.post(
            "http://localhost:8051/mcp",
            json=init_payload,
            headers=headers,
            timeout=30
        )

        print(f"Init response: {response.status_code}")

        if response.status_code == 200:
            init_data = response.json()
            print(f"✅ Session initialized successfully")
            print(f"Server capabilities: {json.dumps(init_data.get('result', {}), indent=2)}")
            return session_id
        else:
            print(f"❌ Init failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Init request failed: {e}")
        return None

def test_mcp_tools_access(session_id):
    """Test accessing MCP tools with the established session."""
    if not session_id:
        return False

    print(f"\n🔧 Testing tool access with session {session_id[:8]}...")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Session-ID": session_id
    }

    # Test health check tool
    tool_payload = {
        "jsonrpc": "2.0",
        "id": "tool_test",
        "method": "tools/call",
        "params": {
            "name": "health_check",
            "arguments": {}
        }
    }

    try:
        response = requests.post(
            "http://localhost:8051/mcp",
            json=tool_payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Tool call successful!")
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Tool call failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Tool call request failed: {e}")
        return False

def print_cline_mcp_instructions():
    """Print instructions for Cline MCP configuration issues."""
    print("\n📋 Cline MCP Configuration Instructions:")
    print("-" * 50)
    print("1. Cline MCP Settings Location:")
    print("   %APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
    print("")
    print("2. Current Configuration Issues Fixed:")
    print("   ✅ Removed conflicting server configurations")
    print("   ✅ Standardized URLs (localhost vs 127.0.0.1)")
    print("   ✅ Fixed session management protocol")
    print("   ✅ Removed invalid token placeholders")
    print("")
    print("3. If issues persist:")
    print("   • Restart VS Code completely")
    print("   • Check Developer Tools Console for Cline MCP errors")
    print("   • Verify MCP server is running: python -m uvicorn main:app --host 0.0.0.0 --port 8051")
    print("   • Test with troubleshooting script: python mcp_troubleshooting_guide.py")

def run_diagnostics():
    """Run complete MCP diagnostics suite."""
    print("🚀 MCP Connection Diagnostics")
    print("=" * 50)

    # Check if server is running
    server_running = check_mcp_server_status()

    if not server_running:
        print("\n❌ DIAGNOSIS: MCP server is not running")
        print("SOLUTION: Start MCP server first")
        print("Command: python -m uvicorn main:app --host 0.0.0.0 --port 8051")
        return

    # Test configuration compatibility
    session_id = test_mcp_configuration_compatibility()

    if not session_id:
        print("\n❌ DIAGNOSIS: Protocol compatibility issue")
        print("SOLUTION: Check MCP server implementation for Cline protocol support")
        return

    # Test tool access
    tools_working = test_mcp_tools_access(session_id)

    if tools_working:
        print("\n✅ DIAGNOSIS: MCP connection is fully functional!")
        print("SUCCESS: Cline should now be able to connect to MCP tools")
    else:
        print("\n❌ DIAGNOSIS: Tool access issue")
        print("SOLUTION: Check MCP tool implementations and permissions")

    print_cline_mcp_instructions()

if __name__ == "__main__":
    run_diagnostics()
