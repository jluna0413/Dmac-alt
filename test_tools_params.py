#!/usr/bin/env python3
"""
Test tools/list with different parameter combinations
"""

import json
import requests

def test_tools_list_params():
    """Test tools/list with different parameters"""
    mcp_url = "http://localhost:8051/mcp"

    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "Test", "version": "1.0"}
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    response = requests.post(mcp_url, json=init_request, headers=headers)
    session_id = response.headers.get('mcp-session-id')

    if session_id is not None:
        headers["mcp-session-id"] = session_id
    else:
        raise ValueError("Failed to get session ID from MCP initialization")

    print(f"Using session ID: {session_id}")

    # Test 1: No params
    print("\n🧪 Test 1: tools/list with no params")
    request1 = {"jsonrpc": "2.0", "id": "test1", "method": "tools/list"}
    resp1 = requests.post(mcp_url, json=request1, headers=headers)
    print(f"Status: {resp1.status_code}, Response: {resp1.text[:200]}...")

    # Test 2: Empty params
    print("\n🧪 Test 2: tools/list with empty params")
    request2 = {"jsonrpc": "2.0", "id": "test2", "method": "tools/list", "params": {}}
    resp2 = requests.post(mcp_url, json=request2, headers=headers)
    print(f"Status: {resp2.status_code}, Response: {resp2.text[:200]}...")

    # Test 3: Try list_tools instead
    print("\n🧪 Test 3: list_tools method")
    request3 = {"jsonrpc": "2.0", "id": "test3", "method": "list_tools"}
    resp3 = requests.post(mcp_url, json=request3, headers=headers)
    print(f"Status: {resp3.status_code}, Response: {resp3.text[:200]}...")

    # Test 4: Try get_tools
    print("\n🧪 Test 4: get_tools method")
    request4 = {"jsonrpc": "2.0", "id": "test4", "method": "get_tools"}
    resp4 = requests.post(mcp_url, json=request4, headers=headers)
    print(f"Status: {resp4.status_code}, Response: {resp4.text[:200]}...")

    # Test 5: Try without session header
    print("\n🧪 Test 5: tools/list without session (should fail)")
    headers_no_session = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    request5 = {"jsonrpc": "2.0", "id": "test5", "method": "tools/list"}
    resp5 = requests.post(mcp_url, json=request5, headers=headers_no_session)
    print(f"Status: {resp5.status_code}, Response: {resp5.text[:100]}...")

if __name__ == "__main__":
    test_tools_list_params()
