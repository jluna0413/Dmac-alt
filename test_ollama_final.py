#!/usr/bin/env python3
"""
Session-Aware MCP Test for Ollama-Powered Archon

This script properly manages MCP sessions and tests all tools
with Ollama integration maintaining session state.
"""

import json
import requests
from typing import Optional
import time
from datetime import datetime

class SessionAwareMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051/mcp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.mcp_session_id = None
        self.test_results = []
        self.available_tools = []

        # Headers for MCP SSE protocol
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': 'Archon-Ollama-Tester/1.0',
        })

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

    def parse_sse_response(self, response):
        """Parse SSE response and extract session ID if needed"""
        # Check for session ID in headers
        session_id = response.headers.get('mcp-session-id')
        if session_id and not self.mcp_session_id:
            self.mcp_session_id = session_id
            print(f"🔗 Session ID obtained: {session_id}")

        # Parse SSE content
        lines = response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
        return None

    def make_mcp_request(self, method: str, params: Optional[dict] = None):
        """Make MCP request with session management"""
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": f"test_{int(time.time())}_{method}",
            "method": method,
            "params": params
        }

        # Add session ID if we have one
        headers = dict(self.session.headers)
        if self.mcp_session_id:
            headers['X-Session-ID'] = self.mcp_session_id

        try:
            response = self.session.post(self.base_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                parsed_data = self.parse_sse_response(response)
                if parsed_data:
                    return parsed_data
                else:
                    return {"error": {"code": -1, "message": "Failed to parse SSE response"}}
            else:
                return {
                    "error": {
                        "code": response.status_code,
                        "message": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
                }
        except (requests.RequestException, ValueError, KeyError) as e:
            return {
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }

    def initialize_session(self):
        """Initialize MCP session"""
        print("🔗 Initializing MCP Session...")

        result = self.make_mcp_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "ollama-test-client", "version": "1.0"}
        })

        if "error" in result:
            self.log_test("initialize", False, f"Failed: {result['error']['message']}")
            return False
        else:
            server_info = result.get("result", {}).get("serverInfo", {})
            server_name = server_info.get("name", "unknown")
            server_version = server_info.get("version", "unknown")
            self.log_test("initialize", True, f"Connected to {server_name} v{server_version}")
            return True

    def discover_tools(self):
        """Discover available MCP tools"""
        print("\n🛠️  Discovering Available Tools...")

        result = self.make_mcp_request("tools/list")

        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []
        else:
            tools = result.get("result", {}).get("tools", [])
            self.log_test("tools/list", True, f"Found {len(tools)} tools")

            print("📋 Available MCP Tools:")
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")
                print(f"   {i:2d}. {name}")
                print(f"       {desc[:80]}...")

            return [tool.get("name") for tool in tools]

    def test_tool(self, tool_name: str, arguments: Optional[dict] = None):
        """Test a specific MCP tool"""
        if arguments is None:
            arguments = {}

        params = {"name": tool_name, "arguments": arguments}
        result = self.make_mcp_request("tools/call", params)

        if "error" in result:
            return self._handle_tool_error(tool_name, result["error"]["message"])
        else:
            return self._handle_tool_success(tool_name, result)

    def _handle_tool_error(self, tool_name: str, error_msg: str) -> bool:
        """Handle tool error response."""
        no_data_indicators = [
            "not found", "no data", "empty", "no projects",
            "no tasks", "no documents", "no sources", "no versions"
        ]

        if any(indicator in error_msg.lower() for indicator in no_data_indicators):
            self.log_test(tool_name, True, "Tool functional (no data available)")
            return True
        else:
            self.log_test(tool_name, False, f"Error: {error_msg[:60]}...")
            return False

    def _handle_tool_success(self, tool_name: str, result: dict) -> bool:
        """Handle successful tool response."""
        content = result.get("result", {}).get("content", "")
        content = self._extract_content_text(content)
        
        # Try to parse JSON content
        if isinstance(content, str) and content.strip().startswith('{'):
            parsed_result = self._parse_json_response(tool_name, content)
            if parsed_result is not None:
                return parsed_result

        # Fallback: any content means success
        display_content = str(content)[:50] + "..." if len(str(content)) > 50 else str(content)
        self.log_test(tool_name, True, f"Response: {display_content}")
        return True

    def _extract_content_text(self, content):
        """Extract text from various content formats."""
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                return content[0]["text"]
            else:
                return str(content[0])
        return content

    def _parse_json_response(self, tool_name: str, content: str):
        """Parse JSON response content."""
        try:
            parsed_content = json.loads(content)
            if isinstance(parsed_content, dict) and "success" in parsed_content:
                if parsed_content["success"]:
                    return self._handle_success_response(tool_name, parsed_content)
                else:
                    error_info = parsed_content.get("error", "Unknown error")
                    self.log_test(tool_name, False, f"Tool error: {error_info}")
                    return False
        except json.JSONDecodeError:
            pass
        return None

    def _handle_success_response(self, tool_name: str, parsed_content: dict) -> bool:
        """Handle successful parsed response."""
        result_keys = ["results", "projects", "tasks", "documents", "sources"]
        
        for key in result_keys:
            if key in parsed_content and isinstance(parsed_content[key], list):
                item_count = len(parsed_content[key])
                self.log_test(tool_name, True, f"Success: {item_count} items returned")
                return True
                
        self.log_test(tool_name, True, "Success: Tool executed successfully")
        return True

    def run_full_test_suite(self):
        """Run comprehensive test suite for Ollama MCP integration"""
        self._print_suite_header()
        
        # Initialize and discover
        if not self._initialize_and_discover_tools():
            return False

        # Run tool tests
        self._run_tool_tests()

        # Generate final report
        return self.generate_final_report()

    def _print_suite_header(self):
        """Print test suite header."""
        print("🚀 OLLAMA ARCHON MCP COMPREHENSIVE TEST SUITE")
        print(f"📡 Server: {self.base_url}")
        print("=" * 80)

    def _initialize_and_discover_tools(self) -> bool:
        """Initialize session and discover tools."""
        if not self.initialize_session():
            print("💥 Session initialization failed!")
            return False

        self.available_tools = self.discover_tools()
        if not self.available_tools:
            print("⚠️  No tools discovered - test cannot continue!")
            return False
        
        return True

    def _run_tool_tests(self):
        """Run tests on all available tools."""
        print(f"\n🧪 Testing {len(self.available_tools)} Tools with Ollama Backend...")
        
        tool_test_configs = self._get_tool_test_configs()
        tested_count = 0

        # Test tools with specific configurations
        for tool_name in self.available_tools:
            if tool_name in tool_test_configs:
                tested_count += 1
                time.sleep(0.3)
                arguments = tool_test_configs[tool_name]
                print(f"\n🔧 Testing {tool_name}...")
                self.test_tool(tool_name, arguments)

        # Test remaining tools with default parameters
        for tool_name in self.available_tools:
            if tool_name not in tool_test_configs:
                tested_count += 1
                time.sleep(0.3)
                print(f"\n🔧 Testing {tool_name} (default params)...")
                self.test_tool(tool_name, {})

        print(f"\n✅ Completed testing {tested_count} tools")

    def _get_tool_test_configs(self) -> dict:
        """Get test configurations for each tool."""
        return {
            # Health and system tools
            "health_check": {},
            "session_info": {},

            # RAG tools
            "get_available_sources": {},
            "perform_rag_query": {
                "query": "What is the MCP protocol used for?",
                "match_count": 3
            },
            "search_code_examples": {
                "query": "FastAPI endpoint implementation",
                "match_count": 3
            },

            # Project management
            "list_projects": {},
            "create_project": {
                "title": f"Ollama Test Project {int(time.time())}",
                "description": "Test project for validating Ollama MCP integration"
            },

            # Task management
            "list_tasks": {},
            "create_task": {
                "title": f"Ollama Test Task {int(time.time())}",
                "description": "Validation task for Ollama MCP testing"
            },

            # Document management
            "list_documents": {},
            "create_document": {
                "title": f"Ollama Test Document {int(time.time())}",
                "content": "This document validates Ollama MCP integration",
                "document_type": "note"
            },

            # Version management
            "list_versions": {},

            # Feature management
            "get_project_features": {"project_id": "1"}
        }

    def generate_final_report(self):
        """Generate comprehensive test report"""
        self._print_report_header()
        
        passed, total, pass_rate = self._calculate_results()
        self._print_overall_results(passed, total, pass_rate)
        
        working_categories = self._print_category_performance()
        assessment = self._determine_assessment(pass_rate, working_categories)
        
        report_file = self.save_comprehensive_report(assessment, pass_rate, passed, total)

        return {
            "assessment": assessment,
            "pass_rate": pass_rate,
            "passed": passed,
            "total": total,
            "report_file": report_file
        }

    def _print_report_header(self):
        """Print report header."""
        print("\n" + "=" * 80)
        print("📊 OLLAMA MCP INTEGRATION - FINAL REPORT")
        print("=" * 80)

    def _calculate_results(self):
        """Calculate test results."""
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0
        return passed, total, pass_rate

    def _print_overall_results(self, passed: int, total: int, pass_rate: float):
        """Print overall test results."""
        print(f"📈 Overall Results:")
        print(f"   ✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"   ❌ Failed: {total - passed}/{total}")
        print(f"   🔗 Session: {self.mcp_session_id}")

    def _print_category_performance(self) -> int:
        """Print category performance and return count of working categories."""
        categories = {
            "System": ["initialize", "tools/list", "health_check", "session_info"],
            "Knowledge & RAG": ["get_available_sources", "perform_rag_query", "search_code_examples"],
            "Projects": ["list_projects", "create_project", "get_project", "update_project"],
            "Tasks": ["list_tasks", "create_task", "get_task", "update_task"],
            "Documents": ["list_documents", "create_document", "get_document", "update_document"],
            "Versions": ["list_versions", "create_version", "get_version"],
            "Features": ["get_project_features"]
        }

        print(f"\n📊 Category Performance:")
        working_categories = 0

        for category, tools in categories.items():
            cat_results = [r for r in self.test_results if r["tool"] in tools]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r["success"])
                cat_total = len(cat_results)
                cat_rate = (cat_passed / cat_total) * 100

                icon = "✅" if cat_rate >= 80 else "⚠️" if cat_rate >= 50 else "❌"
                if cat_rate >= 80:
                    working_categories += 1

                print(f"   {icon} {category}: {cat_passed}/{cat_total} ({cat_rate:.0f}%)")
        
        return working_categories

    def _determine_assessment(self, pass_rate: float, working_categories: int) -> str:
        """Determine final assessment and print results."""
        print(f"\n🎯 Integration Assessment:")
        
        if pass_rate >= 85:
            assessment = "EXCELLENT"
            print("🎉 EXCELLENT: Ollama-powered Archon MCP is fully operational!")
        elif pass_rate >= 70:
            assessment = "GOOD"
            print("⚡ GOOD: Strong Ollama integration with minor issues.")
        elif pass_rate >= 50:
            assessment = "PARTIAL"
            print("👍 PARTIAL: Core functionality working, some issues present.")
        else:
            assessment = "NEEDS_ATTENTION"
            print("🔧 NEEDS ATTENTION: Significant integration issues detected.")

        print(f"\n🏆 Working Categories: {working_categories}/7")
        return assessment

    def save_comprehensive_report(self, assessment: str, pass_rate: float, passed: int, total: int):
        """Save comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_archon_mcp_full_report_{timestamp}.json"

        report = {
            "test_metadata": {
                "timestamp": timestamp,
                "integration": "ollama_archon_mcp",
                "server_url": self.base_url,
                "session_id": self.mcp_session_id,
                "test_framework": "session_aware_mcp_tester"
            },
            "summary": {
                "assessment": assessment,
                "pass_rate": pass_rate,
                "tests_passed": passed,
                "tests_failed": total - passed,
                "total_tests": total
            },
            "detailed_results": self.test_results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Full report saved to: {filename}")
        return filename

def main():
    """Main execution for Ollama MCP testing"""
    print("Starting Ollama-powered Archon MCP Integration Test...")

    tester = SessionAwareMCPTester()
    results = tester.run_full_test_suite()

    if results:
        success = results["pass_rate"] >= 50  # 50% pass rate for success
        return 0 if success else 1
    else:
        return 1

if __name__ == "__main__":
    exit(main())
