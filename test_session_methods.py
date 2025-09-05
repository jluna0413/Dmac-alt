#!/usr/bin/env python3
"""
Test MCP session establishment with different approaches

This script validates various methods of session management in the Model Context Protocol (MCP),
testing different ways to pass session identifiers and maintain protocol state.

Features:
- Multiple session ID passing methods validation
- Proper MCP protocol initialization
- Comprehensive error handling and reporting
- Environment variable configuration support

Usage:
    # Basic usage with default server
    python test_session_methods.py
    
    # Custom MCP server URL
    export MCP_SERVER_URL="http://your-server:8051/mcp"
    python test_session_methods.py

Test Approaches:
1. Session ID in request body
2. Session ID in X-Session-ID header  
3. Session ID in mcp-session-id header
4. Session ID in params object
"""

import os
import requests
from typing import Dict, Any, Optional

def test_session_approaches() -> None:
    """
    Test different ways to handle MCP sessions with comprehensive validation.
    
    This function tests multiple approaches for session management in MCP:
    1. Session ID embedded in request body
    2. Session ID passed via X-Session-ID header
    3. Session ID passed via mcp-session-id header  
    4. Session ID embedded in params object
    
    Each approach is validated for compatibility and proper response handling.
    """
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp")
    
    print(f"🚀 MCP Session Methods Test Suite")
    print(f"📡 Testing server: {mcp_url}")
    print("=" * 60)

    # Initialize session with proper MCP protocol handshake
    session_id = initialize_mcp_session(mcp_url)
    if not session_id:
        print("❌ Failed to initialize MCP session - cannot proceed with tests")
        return

    # Test all session approaches
    test_results = []
    
    # Test approach 1: Session ID in request body
    test_results.append(test_session_in_body(mcp_url, session_id))
    
    # Test approach 2: Session ID in headers (X-Session-ID)
    test_results.append(test_session_in_x_header(mcp_url, session_id))
    
    # Test approach 3: Session ID in mcp-session-id header
    test_results.append(test_session_in_mcp_header(mcp_url, session_id))
    
    # Test approach 4: Session ID in params
    test_results.append(test_session_in_params(mcp_url, session_id))
    
    # Display results summary
    print_test_summary(test_results)


def initialize_mcp_session(mcp_url: str) -> Optional[str]:
    """
    Initialize MCP session with proper protocol handshake.
    
    Args:
        mcp_url: The MCP server endpoint URL
        
    Returns:
        Optional[str]: Session ID if successful, None if failed
    """
    init_request = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "Session-Tester", "version": "1.0.0"}
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    print("🔄 Step 1: Initialize MCP session...")
    
    try:
        response = requests.post(mcp_url, json=init_request, headers=headers, timeout=10)
        
        if response.status_code == 200:
            session_id = response.headers.get('mcp-session-id')
            print(f"✅ Session initialized successfully")
            print(f"📝 Session ID: {session_id}")
            return session_id
        else:
            print(f"❌ Initialization failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return None
            
    except (requests.RequestException, requests.Timeout) as e:
        print(f"❌ Network error during initialization: {e}")
        return None


def test_session_in_body(mcp_url: str, session_id: str) -> Dict[str, Any]:
    """
    Test session ID passed in request body.
    
    Args:
        mcp_url: The MCP server endpoint URL
        session_id: Session identifier to test
        
    Returns:
        Dict containing test results
    """
    print("\n🧪 Test 1: Session ID in request body...")
    
    tools_request_body = {
        "jsonrpc": "2.0",
        "id": "tools-1",
        "method": "tools/list",
        "sessionId": session_id
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    try:
        response = requests.post(mcp_url, json=tools_request_body, headers=headers, timeout=10)
        success = response.status_code == 200
        
        result = {
            "method": "Session ID in body",
            "success": success,
            "status_code": response.status_code,
            "response_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
        
        print(f"{'✅' if success else '❌'} Status: {response.status_code}")
        print(f"Response preview: {result['response_preview']}")
        return result
        
    except (requests.RequestException, requests.Timeout) as e:
        result = {
            "method": "Session ID in body",
            "success": False,
            "error": str(e),
            "response_preview": f"Network error: {e}"
        }
        print(f"❌ Network error: {e}")
        return result


def test_session_in_x_header(mcp_url: str, session_id: str) -> Dict[str, Any]:
    """
    Test session ID passed via X-Session-ID header.
    
    Args:
        mcp_url: The MCP server endpoint URL
        session_id: Session identifier to test
        
    Returns:
        Dict containing test results
    """
    print("\n🧪 Test 2: Session ID in X-Session-ID header...")
    
    headers_with_session = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Session-ID": session_id
    }

    tools_request_simple = {
        "jsonrpc": "2.0",
        "id": "tools-2",
        "method": "tools/list"
    }

    try:
        response = requests.post(mcp_url, json=tools_request_simple, headers=headers_with_session, timeout=10)
        success = response.status_code == 200
        
        result = {
            "method": "Session ID in X-Session-ID header",
            "success": success,
            "status_code": response.status_code,
            "response_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
        
        print(f"{'✅' if success else '❌'} Status: {response.status_code}")
        print(f"Response preview: {result['response_preview']}")
        return result
        
    except (requests.RequestException, requests.Timeout) as e:
        result = {
            "method": "Session ID in X-Session-ID header",
            "success": False,
            "error": str(e),
            "response_preview": f"Network error: {e}"
        }
        print(f"❌ Network error: {e}")
        return result


def test_session_in_mcp_header(mcp_url: str, session_id: str) -> Dict[str, Any]:
    """
    Test session ID passed via mcp-session-id header.
    
    Args:
        mcp_url: The MCP server endpoint URL
        session_id: Session identifier to test
        
    Returns:
        Dict containing test results
    """
    print("\n🧪 Test 3: Session ID in mcp-session-id header...")
    
    headers_mcp_session = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": session_id
    }

    tools_request_simple = {
        "jsonrpc": "2.0",
        "id": "tools-3",
        "method": "tools/list"
    }

    try:
        response = requests.post(mcp_url, json=tools_request_simple, headers=headers_mcp_session, timeout=10)
        success = response.status_code == 200
        
        result = {
            "method": "Session ID in mcp-session-id header",
            "success": success,
            "status_code": response.status_code,
            "response_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
        
        print(f"{'✅' if success else '❌'} Status: {response.status_code}")
        print(f"Response preview: {result['response_preview']}")
        return result
        
    except (requests.RequestException, requests.Timeout) as e:
        result = {
            "method": "Session ID in mcp-session-id header",
            "success": False,
            "error": str(e),
            "response_preview": f"Network error: {e}"
        }
        print(f"❌ Network error: {e}")
        return result


def test_session_in_params(mcp_url: str, session_id: str) -> Dict[str, Any]:
    """
    Test session ID passed in params object.
    
    Args:
        mcp_url: The MCP server endpoint URL
        session_id: Session identifier to test
        
    Returns:
        Dict containing test results
    """
    print("\n🧪 Test 4: Session ID in params...")
    
    tools_request_params = {
        "jsonrpc": "2.0",
        "id": "tools-4",
        "method": "tools/list",
        "params": {"sessionId": session_id}
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    try:
        response = requests.post(mcp_url, json=tools_request_params, headers=headers, timeout=10)
        success = response.status_code == 200
        
        result = {
            "method": "Session ID in params",
            "success": success,
            "status_code": response.status_code,
            "response_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
        
        print(f"{'✅' if success else '❌'} Status: {response.status_code}")
        print(f"Response preview: {result['response_preview']}")
        return result
        
    except (requests.RequestException, requests.Timeout) as e:
        result = {
            "method": "Session ID in params",
            "success": False,
            "error": str(e),
            "response_preview": f"Network error: {e}"
        }
        print(f"❌ Network error: {e}")
        return result


def print_test_summary(test_results: list) -> None:
    """
    Print comprehensive test results summary.
    
    Args:
        test_results: List of test result dictionaries
    """
    print("\n" + "=" * 60)
    print("📊 SESSION METHODS TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results if result.get("success", False))
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed > 0:
        print(f"\n🎯 Working session methods:")
        for result in test_results:
            if result.get("success", False):
                print(f"   ✅ {result['method']}")
    
    if passed < total:
        print(f"\n⚠️ Failed session methods:")
        for result in test_results:
            if not result.get("success", False):
                print(f"   ❌ {result['method']}")
    
    # Provide recommendations
    if passed == 0:
        print(f"\n💡 Recommendations:")
        print(f"   • Verify MCP server is running and accessible")
        print(f"   • Check protocol version compatibility")
        print(f"   • Ensure proper initialization sequence")
    elif passed < total:
        print(f"\n💡 Partial success - use working methods for production")


if __name__ == "__main__":
    try:
        test_session_approaches()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except (OSError, RuntimeError, ValueError) as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check server availability and network connectivity")
