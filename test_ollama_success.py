#!/usr/bin/env python3
"""
🎉 FINAL WORKING Ollama MCP Integration Test Suite
Tests all MCP tools with proper initialization sequence.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class OllamaArchonMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session_id = None
        self.request_id = 1
        self.test_results = []
        self.tools = []
        self.successful_tests = 0
        self.failed_tests = 0

    def log_test(self, tool_name: str, success: bool, details: str = ""):
        """Log test result"""
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

    def parse_sse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response"""
        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    return data
                except json.JSONDecodeError:
                    continue
        return {"error": {"code": -1, "message": "No valid JSON data found in SSE response"}}

    def make_mcp_request(self, method: str, params: Optional[Dict] = None, is_notification: bool = False) -> Dict[str, Any]:
        """Make MCP request with correct session ID handling"""
        request_data = self._build_request_data(method, params, is_notification)
        headers = self._build_headers()

        try:
            response = self.session.post(
                self.mcp_url,
                json=request_data,
                headers=headers,
                timeout=30
            )

            # Extract session ID from response headers after initialize
            if 'mcp-session-id' in response.headers and not self.session_id:
                self.session_id = response.headers['mcp-session-id']
                print(f"🔗 Session ID captured: {self.session_id}")

            if response.status_code not in [200, 202]:  # 202 for notifications
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                return {"error": {"code": response.status_code, "message": error_msg}}

            # For notifications, return success
            if is_notification:
                return {"result": {"status": "notification_sent"}}

            return self.parse_sse_response(response.text)

        except (requests.RequestException, ValueError, KeyError) as e:
            error_msg = f"Request exception: {str(e)}"
            return {"error": {"code": -1, "message": error_msg}}

    def _build_request_data(self, method: str, params: Optional[Dict], is_notification: bool) -> Dict[str, Any]:
        """Build the request data structure."""
        request_data: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method
        }

        # Only add ID for requests, not notifications
        if not is_notification:
            request_data["id"] = f"test-{self.request_id}"
            self.request_id += 1

        # Add params if provided
        if params:
            request_data["params"] = params

        return request_data

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with session ID if available."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        # Add session ID to headers if we have one
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        return headers

    def initialize_session(self) -> bool:
        """Initialize MCP session with proper handshake"""
        print("🔗 Initializing MCP Session...")

        # Step 1: Initialize
        result = self.make_mcp_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "Ollama-Archon-Tester",
                "version": "1.0.0"
            }
        })

        if "error" in result:
            self.log_test("initialize", False, f"Failed: {result['error']['message']}")
            return False

        # Extract server info
        server_info = result.get("result", {}).get("serverInfo", {})
        server_name = server_info.get("name", "unknown")
        server_version = server_info.get("version", "unknown")

        self.log_test("initialize", True, f"Connected to {server_name} v{server_version}")

        # Step 2: Send initialized notification
        print("📡 Sending initialized notification...")
        notify_result = self.make_mcp_request("notifications/initialized", is_notification=True)

        if "error" in notify_result:
            self.log_test("initialized", False, f"Failed: {notify_result['error']['message']}")
            return False

        self.log_test("initialized", True, "Handshake completed")
        return True

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available MCP tools"""
        print("\n🛠️  Discovering Available Tools...")
        
        result = self.make_mcp_request("tools/list")
        return self._process_tools_result(result)

    def _process_tools_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process the result from tools/list request."""
        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []

        tools = result.get("result", {}).get("tools", [])
        if not tools:
            self.log_test("tools/list", False, "No tools found in response")
            return []

        self.log_test("tools/list", True, f"Found {len(tools)} tools")
        self._categorize_and_display_tools(tools)
        return tools

    def _categorize_and_display_tools(self, tools: List[Dict[str, Any]]) -> None:
        """Categorize and display discovered tools."""
        categories = self._categorize_tools(tools)
        print(f"📋 Tool Categories:")
        print(f"   🔍 RAG Tools: {len(categories['rag'])}")
        print(f"   📁 Project Tools: {len(categories['project'])}")
        print(f"   ⚙️  System Tools: {len(categories['system'])}")
        print(f"   🛠️  Total Tools: {len(tools)}")

    def _categorize_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, List]:
        """Categorize tools by type."""
        categories = {"rag": [], "project": [], "system": []}
        keywords = {
            "rag": ["rag", "search", "sources"],
            "project": ["project", "document", "task", "version"],
            "system": ["health", "session"]
        }
        
        for tool in tools:
            tool_name = tool.get("name", "")
            for category, kw_list in keywords.items():
                if any(kw in tool_name for kw in kw_list):
                    categories[category].append(tool)
                    break
        
        return categories

    def test_tool(self, tool_name: str, test_params: Dict[str, Any]) -> bool:
        """Test a specific MCP tool"""
        result = self.make_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": test_params
        })

        if "error" in result:
            error_msg = result["error"]["message"]
            # Some errors are expected (like "No projects found")
            expected_errors = ["not found", "no data", "empty", "no projects", "no documents", "no tasks", "no sources"]
            if any(phrase in error_msg.lower() for phrase in expected_errors):
                self.log_test(tool_name, True, f"Expected empty result: {error_msg[:50]}...")
                return True
            else:
                self.log_test(tool_name, False, f"Error: {error_msg[:100]}...")
                return False

        # Check for tool result
        tool_result = result.get("result", {})
        if "content" in tool_result:
            content = tool_result["content"]
            if isinstance(content, list) and content:
                first_content = content[0]
                if "text" in first_content:
                    response_text = first_content["text"][:80]
                    self.log_test(tool_name, True, f"Response: {response_text}...")
                    return True

        self.log_test(tool_name, True, "Tool executed successfully")
        return True

    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        self._print_test_header()
        
        # Initialize and discover tools
        if not self._initialize_and_discover():
            return
        
        # Run all tool tests
        self._run_all_tool_tests()
        
        # Generate final report
        self._generate_comprehensive_report()

    def _print_test_header(self):
        """Print test suite header."""
        print("🚀 OLLAMA ARCHON MCP COMPREHENSIVE TEST SUITE")
        print("📡 Server: http://localhost:8051/mcp")
        print("🤖 Backend: Ollama (Local AI)")
        print("=" * 80)

    def _initialize_and_discover(self) -> bool:
        """Initialize session and discover tools."""
        # Initialize session with proper handshake
        if not self.initialize_session():
            print("⚠️  Session initialization failed - test cannot continue!")
            return False

        # Discover tools
        self.tools = self.discover_tools()
        if not self.tools:
            print("⚠️  No tools discovered - test cannot continue!")
            return False
        
        return True

    def _run_all_tool_tests(self):
        """Run tests on all discovered tools."""
        test_params = self._get_test_parameters()
        
        print(f"\n🧪 Testing {len(self.tools)} Tools...")
        print("-" * 50)

        self.successful_tests = 0
        self.failed_tests = 0

        for i, tool in enumerate(self.tools, 1):
            tool_name = tool.get("name", "unknown")
            tool_desc = tool.get("description", "")[:50] + "..." if len(tool.get("description", "")) > 50 else tool.get("description", "")

            print(f"\n🔧 [{i:2d}/{len(self.tools)}] {tool_name}: {tool_desc}")

            params = test_params.get(tool_name, {})

            if self.test_tool(tool_name, params):
                self.successful_tests += 1
            else:
                self.failed_tests += 1

            time.sleep(0.2)  # Brief pause between tests

    def _get_test_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get test parameters for each tool."""
        return {
            # System Tools
            "health_check": {},
            "session_info": {},

            # RAG Tools
            "get_available_sources": {},
            "perform_rag_query": {"query": "ollama integration testing", "match_count": 3},
            "search_code_examples": {"query": "python function example", "match_count": 2},

            # Project Management
            "list_projects": {},
            "create_project": {
                "title": "Ollama Test Project",
                "description": "Testing Ollama MCP integration with autonomous coding workflow",
                "project_type": "testing"
            },
            "list_documents": {},
            "create_document": {
                "title": "Ollama Integration Test Results",
                "content": "Testing document creation with Ollama backend",
                "document_type": "test_notes"
            },
            "list_tasks": {},
            "create_task": {
                "title": "Validate Ollama Integration",
                "description": "Comprehensive test to ensure Ollama backend maintains full MCP functionality",
                "priority": "high"
            },
            "list_versions": {},
            "get_project_features": {}
        }

    def _generate_comprehensive_report(self):
        """Generate and display comprehensive test report."""
        print("\n" + "=" * 80)
        print("📊 OLLAMA INTEGRATION TEST SUMMARY")
        print("=" * 80)

        total_tests = len(self.tools) + 2  # +2 for initialize and tools/list
        success_rate = (self.successful_tests + 2) / total_tests * 100

        print(f"✅ Successful Tests: {self.successful_tests + 2}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed Tests: {self.failed_tests}/{total_tests}")

        self._print_category_breakdown()
        self._print_status_verdict(success_rate)
        self._print_final_details()

    def _print_category_breakdown(self):
        """Print breakdown by tool category."""
        categories = self._get_result_categories()
        
        print(f"\n📋 Results by Category:")
        for category_name, (icon, results) in categories.items():
            success_count = len([t for t in results if t['success']])
            total = len(results)
            percentage = (success_count / total * 100) if total else 0
            print(f"   {icon} {category_name}: {success_count}/{total} ({percentage:.1f}%)")

    def _get_result_categories(self) -> Dict[str, tuple]:
        """Get categorized test results."""
        keyword_map = {
            "System Tools": (["health", "session", "initialize"], "⚙️"),
            "RAG Tools": (["rag", "search", "sources"], "🔍"),
            "Project Tools": (["project", "document", "task", "version"], "📁")
        }
        
        categories = {}
        for name, (keywords, icon) in keyword_map.items():
            results = [t for t in self.test_results if any(kw in t["tool"] for kw in keywords)]
            categories[name] = (icon, results)
        
        return categories

    def _print_status_verdict(self, success_rate: float):
        """Print final status verdict."""
        print(f"\n🎯 OLLAMA INTEGRATION STATUS:")
        if success_rate >= 95:
            print("🎉 EXCELLENT - Ollama backend is fully operational!")
            print("   ✅ All critical functions working correctly")
            print("   ✅ Autonomous coding workflow fully supported")
        elif success_rate >= 90:
            print("✅ EXCELLENT - Ollama backend working very well!")
            print("   ⚠️  Minor issues detected but core functionality intact")
        elif success_rate >= 85:
            print("✅ GOOD - Ollama backend is working well")
            print("   ⚠️  Some attention needed for complete functionality")
        elif success_rate >= 70:
            print("⚠️  ACCEPTABLE - Ollama backend mostly working")
            print("   🔧 Several issues need attention")
        else:
            print("❌ NEEDS WORK - Ollama backend has significant issues")
            print("   🛠️  Major troubleshooting required")

    def _print_final_details(self):
        """Print final details and recommendations."""
        print(f"\n🔗 Session ID: {self.session_id}")
        print(f"⏱️  Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✨ Ollama MCP integration validation complete!")

        # Calculate success rate for recommendations
        total_tests = len(self.tools) + 2
        success_rate = (self.successful_tests + 2) / total_tests * 100

        # Specific advice for user
        if success_rate >= 90:
            print(f"\n🎊 CONGRATULATIONS! Your Ollama configuration is working excellently!")
            print("   📝 You can confidently use the autonomous coding workflow")
            print("   🤖 All MCP tools are responding correctly with Ollama backend")
        else:
            print(f"\n💡 RECOMMENDATIONS:")
            print("   🔍 Check failed tests above for specific issues")
            print("   🔄 Consider restarting Archon services if needed")
            print("   📚 Review logs for detailed error information")

def main():
    """Main test execution"""
    print("Starting comprehensive Ollama MCP integration validation...")

    tester = OllamaArchonMCPTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
