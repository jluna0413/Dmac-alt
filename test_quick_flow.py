#!/usr/bin/env python3
"""
Quick test of the exact working flow
"""

import json
import requests

def test_exact_flow():
    """Test the exact working MCP flow"""
    mcp_url = "http://localhost:8051/mcp"

    # Step 1: Initialize
    init_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    init_request = {
        "jsonrpc": "2.0",
        "id": "init-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "Quick-Test", "version": "1.0.0"}
        }
    }

    print("🔄 Step 1: Initialize...")
    init_response = requests.post(mcp_url, json=init_request, headers=init_headers)
    print(f"Status: {init_response.status_code}")

    session_id = init_response.headers.get('mcp-session-id')
    print(f"Session ID: {session_id}")

    if not session_id:
        print("❌ No session ID received!")
        return

    # Step 2: List tools with session
    tools_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": session_id
    }

    tools_request = {
        "jsonrpc": "2.0",
        "id": "tools-test",
        "method": "tools/list"
    }

    print("\n🔄 Step 2: List tools...")
    tools_response = requests.post(mcp_url, json=tools_request, headers=tools_headers)
    print(f"Status: {tools_response.status_code}")
    print(f"Response preview: {tools_response.text[:300]}...")

    # Parse response
    lines = tools_response.text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    print(f"\n✅ Found {len(tools)} tools:")
                    for tool in tools[:5]:  # Show first 5
                        print(f"   • {tool.get('name', 'unknown')}: {tool.get('description', '')[:60]}...")

                    # Test one tool
                    if tools:
                        test_tool_name = tools[0].get("name", "")
                        print(f"\n🧪 Testing tool: {test_tool_name}")

                        tool_request = {
                            "jsonrpc": "2.0",
                            "id": "tool-test",
                            "method": "tools/call",
                            "params": {
                                "name": test_tool_name,
                                "arguments": {}
                            }
                        }

                        tool_response = requests.post(mcp_url, json=tool_request, headers=tools_headers)
                        print(f"Tool response status: {tool_response.status_code}")
                        print(f"Tool response: {tool_response.text[:200]}...")

                break
            except json.JSONDecodeError:
                continue

if __name__ == "__main__":
    test_exact_flow()
