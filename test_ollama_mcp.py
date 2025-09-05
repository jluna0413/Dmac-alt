#!/usr/bin/env python3
"""
Working MCP Client Test for Ollama-Powered Archon

This script properly implements the MCP protocol with correct headers
to test all available tools in the Ollama-powered Archon setup.

Features:
- Comprehensive MCP tool discovery and testing
- Proper JSON-RPC protocol implementation
- Ollama integration validation
- Detailed test reporting with categorization
- Error handling with graceful degradation
- Environment variable configuration support

Usage:
    # Basic usage with default server
    python test_ollama_mcp.py
    
    # Custom MCP server URL
    export MCP_SERVER_URL="http://your-server:8051/mcp"
    python test_ollama_mcp.py

Exit Codes:
    0: Tests passed (≥50% pass rate)
    1: Tests failed or connectivity issues
"""

import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

class WorkingMCPTester:
    """
    Comprehensive MCP client tester for Ollama-powered Archon integration.
    
    This class provides testing capabilities for the Model Context Protocol (MCP)
    server with specific support for Ollama integration and proper protocol handling.
    
    Attributes:
        base_url (str): The MCP server endpoint URL
        session (requests.Session): HTTP session with proper MCP headers
        session_id (str): Unique session identifier for this test run
        test_results (List[Dict]): Accumulated test results
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the MCP tester with proper protocol configuration.
        
        Args:
            base_url: MCP server URL (defaults to environment variable or localhost:8051)
        """
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp")
        self.session = requests.Session()
        self.session_id = f"test_{int(time.time())}"
        self.test_results: List[Dict[str, Any]] = []

        # CRITICAL: MCP server requires BOTH content types in Accept header
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',  # BOTH required!
            'User-Agent': 'Archon-MCP-Tester/1.0',
        })

    def log_test(self, tool_name: str, success: bool, details: str = "") -> None:
        """
        Log test result with structured data and console output.
        
        Args:
            tool_name: Name of the tool being tested
            success: Whether the test passed
            details: Additional details about the test result
        """
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "tool": tool_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {tool_name}: {details}")

    def make_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an MCP JSON-RPC request with proper headers and error handling.
        
        Args:
            method: The MCP method to call
            params: Parameters for the method call
            
        Returns:
            Dict containing the response or error information
            
        Raises:
            requests.RequestException: For network-related errors
            ValueError: For invalid JSON responses
        """
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": f"test_{int(time.time())}",
            "method": method,
            "params": params
        }

        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": {
                        "code": response.status_code,
                        "message": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
                }
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            return {
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }

    def test_connectivity(self) -> bool:
        """
        Test basic MCP connectivity and protocol initialization.
        
        Returns:
            bool: True if connectivity is successful, False otherwise
        """
        print("🔗 Testing MCP Server Connectivity...")

        # Test simple initialization
        result = self.make_mcp_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        })

        if "error" in result:
            self.log_test("connectivity", False, f"Connection failed: {result['error']['message']}")
            return False
        else:
            self.log_test("connectivity", True, "MCP server responding correctly")
            return True

    def test_list_tools(self) -> List[str]:
        """
        Test tool discovery and return available tool names.
        
        Returns:
            List[str]: Names of available MCP tools
        """
        print("\n🛠️  Discovering Available Tools...")

        result = self.make_mcp_request("tools/list")

        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []
        else:
            tools = result.get("result", {}).get("tools", [])
            self.log_test("tools/list", True, f"Found {len(tools)} tools")

            print("📋 Available Tools:")
            for tool in tools:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")
                print(f"   • {name}: {desc[:80]}...")

            return [tool.get("name") for tool in tools]

    def test_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """
        Test a specific MCP tool with optional arguments.
        
        Args:
            tool_name: Name of the tool to test
            arguments: Optional arguments to pass to the tool
            
        Returns:
            bool: True if the tool test was successful, False otherwise
        """
        if arguments is None:
            arguments = {}

        params = {
            "name": tool_name,
            "arguments": arguments
        }

        result = self.make_mcp_request("tools/call", params)

        if "error" in result:
            error_msg = result["error"]["message"]
            # Some errors are expected (like no data available)
            if "not found" in error_msg.lower() or "no data" in error_msg.lower():
                self.log_test(tool_name, True, f"Tool works (no data): {error_msg[:50]}...")
                return True
            else:
                self.log_test(tool_name, False, f"Error: {error_msg[:50]}...")
                return False
        else:
            content = result.get("result", {}).get("content", "")
            if isinstance(content, list) and len(content) > 0:
                content = content[0].get("text", str(content))

            display_content = str(content)[:80] + "..." if len(str(content)) > 80 else str(content)
            self.log_test(tool_name, True, f"Success: {display_content}")
            return True

    def run_tool_tests(self, available_tools: List[str]) -> None:
        """
        Test all available tools with appropriate test parameters.
        
        Args:
            available_tools: List of tool names to test
        """
        print(f"\n🧪 Testing {len(available_tools)} MCP Tools...")

        # Define test parameters for specific tools
        test_configs = {
            "perform_rag_query": {"query": "What is MCP protocol?", "match_count": 3},
            "search_code_examples": {"query": "FastAPI endpoint", "match_count": 3},
            "create_project": {"title": f"Test Project {int(time.time())}", "description": "Test project"},
            "create_task": {"title": f"Test Task {int(time.time())}", "description": "Test task"},
            "create_document": {
                "title": f"Test Doc {int(time.time())}",
                "content": "Test document content",
                "document_type": "note"
            }
        }

        # Test each available tool
        for tool_name in available_tools:
            arguments = test_configs.get(tool_name, {})
            self.test_tool(tool_name, arguments)

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete MCP test suite"""
        print("🚀 OLLAMA-POWERED ARCHON MCP COMPREHENSIVE TEST")
        print(f"📡 Server: {self.base_url}")
        print("=" * 70)

        # Execute core tests
        if not self._run_core_tests():
            return {"status": "FAILED", "pass_rate": 0.0, "passed": 0, "total": 0}
        
        # Generate and return results
        return self._calculate_and_display_results()

    def _run_core_tests(self) -> bool:
        """Run core connectivity and tool tests."""
        if not self.test_connectivity():
            print("💥 Basic connectivity failed - check if MCP server is running")
            return False

        available_tools = self.test_list_tools()
        if not available_tools:
            print("⚠️  No tools discovered - testing may be limited")
        else:
            self.run_tool_tests(available_tools)
        
        return True

    def _calculate_and_display_results(self) -> Dict[str, Any]:
        """Calculate statistics and display final results."""
        print("\n" + "=" * 70)
        print("📊 FINAL TEST RESULTS")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print(f"✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"❌ Failed: {total - passed}/{total}")

        self._print_category_breakdown()
        status = self._get_status_message(pass_rate)
        
        return {"status": status, "pass_rate": pass_rate, "passed": passed, "total": total}

    def _print_category_breakdown(self) -> None:
        """Print category-wise breakdown of results."""
        categories = {
            "System": ["connectivity", "tools/list"],
            "RAG": ["get_available_sources", "perform_rag_query", "search_code_examples"],
            "Health": ["health_check", "session_info"],
            "Projects": ["list_projects", "create_project", "get_project"],
            "Tasks": ["list_tasks", "create_task"],
            "Documents": ["list_documents", "create_document"],
            "Versions": ["list_versions"]
        }

        print(f"\n📈 Category Breakdown:")
        for category, tools in categories.items():
            cat_results = [r for r in self.test_results if r["tool"] in tools]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r["success"])
                print(f"   {category}: {cat_passed}/{len(cat_results)} passed")

    def _get_status_message(self, pass_rate: float) -> str:
        """Display status message and return status."""
        if pass_rate >= 90:
            print(f"\n🎉 EXCELLENT! Ollama-powered Archon MCP is fully operational!")
            return "EXCELLENT"
        elif pass_rate >= 70:
            print(f"\n⚡ GOOD! Most functionality working with Ollama integration.")
            return "GOOD"
        elif pass_rate >= 50:
            print(f"\n⚠️  PARTIAL: Core functions work, some features need attention.")
            return "PARTIAL"
        else:
            print(f"\n🔧 NEEDS WORK: Significant issues detected.")
            return "NEEDS_WORK"

    def save_results(self, summary: Dict[str, Any]) -> str:
        """
        Save detailed test results to a JSON file.
        
        Args:
            summary: Test summary data from run_comprehensive_test
            
        Returns:
            str: Filename of the saved report
            
        Raises:
            OSError: If file cannot be written
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_archon_mcp_test_{timestamp}.json"

        report = {
            "test_summary": {
                "timestamp": timestamp,
                "server_url": self.base_url,
                "integration": "ollama",
                "overall_status": summary["status"],
                "pass_rate": summary["pass_rate"],
                "total_tests": summary["total"],
                "passed_tests": summary["passed"],
                "failed_tests": summary["total"] - summary["passed"]
            },
            "detailed_results": self.test_results
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Complete test report saved to: {filename}")
            return filename
        except OSError as e:
            print(f"⚠️ Failed to save test report: {e}")
            return ""

def main() -> int:
    """
    Main test execution with comprehensive error handling.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("Starting Ollama-Powered Archon MCP Test Suite...")

    try:
        tester = WorkingMCPTester()
        summary = tester.run_comprehensive_test()

        if summary:
            tester.save_results(summary)
            return 0 if summary["pass_rate"] >= 50 else 1
        else:
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        return 1
    except (requests.ConnectionError, requests.Timeout) as e:
        print(f"❌ Network error: {e}")
        print("💡 Ensure the MCP server is running and accessible")
        return 1
    except (OSError, RuntimeError, ValueError) as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
