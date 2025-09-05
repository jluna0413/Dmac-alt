#!/usr/bin/env python3
"""
Test proper MCP initialization with 'initialized' notification
"""

import json
import requests

def test_proper_initialization():
    """Test proper MCP initialization sequence"""
    mcp_url = "http://localhost:8051/mcp"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    # Step 1: Initialize
    print("🔄 Step 1: Initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "Proper-Test", "version": "1.0"}
        }
    }

    response = requests.post(mcp_url, json=init_request, headers=headers)
    session_id = response.headers.get('mcp-session-id')
    print(f"Session ID: {session_id}")

    if session_id is not None:
        headers["mcp-session-id"] = session_id
    else:
        raise ValueError("Failed to get session ID from MCP initialization")

    # Step 2: Send 'initialized' notification
    print("\n🔄 Step 2: Send initialized notification...")
    initialized_request = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }

    response2 = requests.post(mcp_url, json=initialized_request, headers=headers)
    print(f"Initialized status: {response2.status_code}")

    # Step 3: Now try tools/list
    print("\n🔄 Step 3: List tools...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": "tools-list",
        "method": "tools/list"
    }

    response3 = requests.post(mcp_url, json=tools_request, headers=headers)
    print(f"Tools status: {response3.status_code}")
    print(f"Tools response: {response3.text[:300]}...")

    # Parse tools response
    lines = response3.text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    print(f"\n✅ SUCCESS! Found {len(tools)} tools:")
                    for i, tool in enumerate(tools[:3]):  # Show first 3
                        print(f"   {i+1}. {tool.get('name', 'unknown')}: {tool.get('description', '')[:50]}...")

                    # Test one tool
                    if tools:
                        test_tool = tools[0].get("name", "")
                        print(f"\n🧪 Testing tool: {test_tool}")

                        tool_request = {
                            "jsonrpc": "2.0",
                            "id": "tool-test",
                            "method": "tools/call",
                            "params": {
                                "name": test_tool,
                                "arguments": {}
                            }
                        }

                        tool_response = requests.post(mcp_url, json=tool_request, headers=headers)

                        # Parse tool response
                        tool_lines = tool_response.text.strip().split('\n')
                        for tool_line in tool_lines:
                            if tool_line.startswith('data: '):
                                try:
                                    tool_data = json.loads(tool_line[6:])
                                    if "result" in tool_data:
                                        print(f"✅ Tool {test_tool} executed successfully!")
                                        content = tool_data["result"].get("content", [])
                                        if content and content[0].get("text"):
                                            text = content[0]["text"][:100]
                                            print(f"   Response: {text}...")
                                    elif "error" in tool_data:
                                        error = tool_data["error"]["message"]
                                        print(f"⚠️  Tool {test_tool} error: {error}")
                                    break
                                except json.JSONDecodeError:
                                    continue

                    return True
                elif "error" in data:
                    print(f"❌ Error: {data['error']['message']}")
                    return False
                break
            except json.JSONDecodeError:
                continue

    return False

if __name__ == "__main__":
    test_proper_initialization()
