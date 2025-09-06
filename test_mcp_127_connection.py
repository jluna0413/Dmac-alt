#!/usr/bin/env python3
"""
Test MCP connection using 127.0.0.1 instead of localhost
"""

import requests
import json

def test_mcp_connection():
    """Test MCP server connection"""
    url = "http://127.0.0.1:8051/mcp"

    # Test data from the original test script
    payload = {
        "jsonrpc": "2.0",
        "id": f"test_health_{int(__import__('time').time())}",
        "method": "tools/call",
        "params": {
            "name": "health_check",
            "arguments": {}
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Session-ID": f"test_session_{int(__import__('time').time())}"
    }

    print(f"Testing MCP connection to: {url}")
    print(f"Request payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response JSON: {json.dumps(data, indent=2)}")
                print("✅ MCP server is working correctly!")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} error")
            print(f"Response body: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_mcp_connection()
