#!/usr/bin/env python3
"""
Test MCP connection with proper session initialization
"""

import json
import requests
import time
import uuid

def test_mcp_connection_with_session():
    """Test MCP server connection with proper session initialization"""
    mcp_url = "http://127.0.0.1:8051/mcp"

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    # Step 1: Initialize session first
    init_payload = {
        "jsonrpc": "2.0",
        "id": f"init_{int(time.time())}",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "MCP-Test-Client",
                "version": "1.0.0"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Session-ID": session_id
    }

    print("Step 1: Initializing MCP session...")
    print(f"URL: {mcp_url}")
    print(f"Session ID: {session_id}")
    print(f"Request: {json.dumps(init_payload, indent=2)}")

    try:
        response = requests.post(mcp_url, json=init_payload, headers=headers, timeout=30)
        print(f"Init response status: {response.status_code}")
        print(f"Init response headers: {dict(response.headers)}")

        if response.status_code == 200:
            init_data = response.json()
            print(f"Init response: {json.dumps(init_data, indent=2)}")
        else:
            print(f"❌ Init failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Init request failed: {e}")
        return False

    # Step 2: Try to call tools/call with session
    tool_payload = {
        "jsonrpc": "2.0",
        "id": f"tool_{int(time.time())}",
        "method": "tools/call",
        "params": {
            "name": "health_check",
            "arguments": {}
        }
    }

    print("\nStep 2: Calling tool with established session...")
    print(f"Request: {json.dumps(tool_payload, indent=2)}")

    try:
        response = requests.post(mcp_url, json=tool_payload, headers=headers, timeout=30)
        print(f"Tool call response status: {response.status_code}")

        if response.status_code == 200:
            tool_data = response.json()
            print(f"Tool response: {json.dumps(tool_data, indent=2)}")
            print("✅ MCP connection successful!")
            return True
        else:
            print(f"❌ Tool call failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Tool call request failed: {e}")
        return False

if __name__ == "__main__":
    test_mcp_connection_with_session()
