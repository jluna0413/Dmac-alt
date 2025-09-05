#!/usr/bin/env python3
"""
Test calling tools directly instead of listing them first
"""

import json
import requests

def test_direct_tool_calls():
    """Test calling tools directly without listing them first"""
    mcp_url = "http://localhost:8051/mcp"

    # Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "Direct-Test", "version": "1.0"}
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    response = requests.post(mcp_url, json=init_request, headers=headers)
    session_id = response.headers.get('mcp-session-id')

    headers["mcp-session-id"] = session_id
    print(f"Session ID: {session_id}")

    # Test direct tool calls based on the tool names we know exist
    known_tools = [
        "health_check",
        "session_info",
        "list_projects",
        "get_available_sources",
        "perform_rag_query"
    ]

    for tool_name in known_tools:
        print(f"\n🧪 Testing tool: {tool_name}")

        tool_request = {
            "jsonrpc": "2.0",
            "id": f"test-{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {}
            }
        }

        if tool_name == "perform_rag_query":
            tool_request["params"]["arguments"] = {"query": "test", "match_count": 1}

        tool_response = requests.post(mcp_url, json=tool_request, headers=headers)
        print(f"Status: {tool_response.status_code}")

        # Parse response
        lines = tool_response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if "result" in data:
                        print(f"✅ Success: {tool_name}")
                        result = data["result"]
                        if "content" in result:
                            content = result["content"]
                            if content and isinstance(content, list) and content[0].get("text"):
                                text = content[0]["text"][:100]
                                print(f"   Response: {text}...")
                        break
                    elif "error" in data:
                        error = data["error"]["message"]
                        print(f"❌ Error: {error}")
                        break
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    test_direct_tool_calls()
