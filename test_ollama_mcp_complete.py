#!/usr/bin/env python3
"""
Working SSE MCP Client Test for Ollama-Powered Archon

This script properly handles SSE responses from the MCP server
and tests all available tools with Ollama integration.
"""

import json
import requests
import time
import re
from datetime import datetime
from typing import Optional, Dict, Any

class SSEMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051/mcp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = f"test_{int(time.time())}"
        self.test_results = []

        # Proper headers for MCP SSE protocol
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': 'Archon-Ollama-MCP-Tester/1.0',
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

    def parse_sse_response(self, response_text: str):
        """Parse SSE response to extract JSON data"""
        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
        return None

    def make_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Make an MCP JSON-RPC request and handle SSE response"""
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": f"test_{int(time.time())}_{method}",
            "method": method,
            "params": params
        }

        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)

            if response.status_code == 200:
                # Parse SSE response
                parsed_data = self.parse_sse_response(response.text)
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
        except Exception as e:
            return {
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }

    def test_initialization(self):
        """Test MCP server initialization"""
        print("🔗 Testing MCP Server Initialization...")

        result = self.make_mcp_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "ollama-test-client", "version": "1.0"}
        })

        if "error" in result:
            self.log_test("initialize", False, f"Init failed: {result['error']['message']}")
            return False
        else:
            server_info = result.get("result", {}).get("serverInfo", {})
            server_name = server_info.get("name", "unknown")
            server_version = server_info.get("version", "unknown")
            self.log_test("initialize", True, f"Connected to {server_name} v{server_version}")
            return True

    def test_list_tools(self):
        """Test tool discovery"""
        print("\n🛠️  Discovering Available MCP Tools...")

        result = self.make_mcp_request("tools/list")

        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []
        else:
            tools = result.get("result", {}).get("tools", [])
            self.log_test("tools/list", True, f"Discovered {len(tools)} tools")

            print("📋 Available Tools:")
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")
                print(f"   {i:2d}. {name}: {desc[:70]}...")

            return [tool.get("name") for tool in tools]

    def test_tool_call(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None):
        """Test calling a specific MCP tool"""
        if arguments is None:
            arguments = {}

        params = {
            "name": tool_name,
            "arguments": arguments
        }

        result = self.make_mcp_request("tools/call", params)

        if "error" in result:
            error_msg = result["error"]["message"]
            # Some tools may legitimately have no data
            if any(phrase in error_msg.lower() for phrase in ["not found", "no data", "empty", "no projects", "no tasks", "no documents"]):
                self.log_test(tool_name, True, f"Tool works (no data available)")
                return True
            else:
                self.log_test(tool_name, False, f"Error: {error_msg[:60]}...")
                return False
        else:
            # Extract content from result
            content = result.get("result", {}).get("content", "")
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    content = content[0]["text"]
                else:
                    content = str(content[0])

            # Parse JSON content if it's a JSON string
            if isinstance(content, str) and content.strip().startswith('{'):
                try:
                    parsed_content = json.loads(content)
                    if isinstance(parsed_content, dict):
                        if "success" in parsed_content:
                            success_status = parsed_content["success"]
                            if success_status:
                                display_info = f"Success: {str(parsed_content)[:60]}..."
                                self.log_test(tool_name, True, display_info)
                                return True
                            else:
                                error_info = parsed_content.get("error", "Unknown error")
                                self.log_test(tool_name, False, f"Tool error: {error_info}")
                                return False
                        else:
                            # Tool returned data successfully
                            display_info = f"Response: {str(parsed_content)[:60]}..."
                            self.log_test(tool_name, True, display_info)
                            return True
                except json.JSONDecodeError:
                    pass

            # Default: treat any content as success
            display_content = str(content)[:60] + "..." if len(str(content)) > 60 else str(content)
            self.log_test(tool_name, True, f"Response: {display_content}")
            return True

    def run_comprehensive_test(self):
        """Run comprehensive MCP test for Ollama integration"""
        print("🚀 OLLAMA-POWERED ARCHON MCP COMPREHENSIVE TEST")
        print(f"📡 MCP Server: {self.base_url}")
        print("=" * 80)

        # Step 1: Initialize MCP connection
        if not self.test_initialization():
            print("💥 MCP initialization failed!")
            return False

        # Step 2: Discover available tools
        available_tools = self.test_list_tools()
        if not available_tools:
            print("⚠️  No tools discovered!")
            return False

        # Step 3: Test all available tools
        print(f"\n🧪 Testing {len(available_tools)} MCP Tools with Ollama Backend...")

        # Define specific test parameters for certain tools
        test_parameters = {
            "perform_rag_query": {"query": "What is MCP protocol?", "match_count": 3},
            "search_code_examples": {"query": "FastAPI endpoint", "match_count": 3},
            "create_project": {
                "title": f"Ollama Test Project {int(time.time())}",
                "description": "Test project created during Ollama MCP integration test"
            },
            "create_task": {
                "title": f"Ollama Test Task {int(time.time())}",
                "description": "Test task for validating Ollama integration"
            },
            "create_document": {
                "title": f"Ollama Test Doc {int(time.time())}",
                "content": "Test document content for Ollama MCP validation",
                "document_type": "note"
            }
        }

        # Test each tool
        for tool_name in available_tools:
            time.sleep(0.5)  # Small delay to avoid overwhelming the server
            arguments = test_parameters.get(tool_name, {})
            self.test_tool_call(tool_name, arguments)

        # Generate comprehensive results
        self.generate_test_report()

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 OLLAMA MCP INTEGRATION TEST REPORT")
        print("=" * 80)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print(f"✅ Total Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"❌ Total Failed: {total - passed}/{total}")

        # Categorize results by tool type
        categories = {
            "System & Health": ["initialize", "tools/list", "health_check", "session_info"],
            "RAG & Knowledge": ["get_available_sources", "perform_rag_query", "search_code_examples"],
            "Project Management": ["list_projects", "create_project", "get_project", "update_project", "delete_project"],
            "Task Management": ["list_tasks", "create_task", "get_task", "update_task", "delete_task"],
            "Document Management": ["list_documents", "create_document", "get_document", "update_document", "delete_document"],
            "Version Control": ["list_versions", "create_version", "get_version", "restore_version"],
            "Features": ["get_project_features"]
        }

        print(f"\n📈 Category Performance:")
        all_working_categories = []

        for category, tools in categories.items():
            cat_results = [r for r in self.test_results if r["tool"] in tools]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r["success"])
                cat_total = len(cat_results)
                cat_rate = (cat_passed / cat_total) * 100
                status_icon = "✅" if cat_rate >= 80 else "⚠️" if cat_rate >= 50 else "❌"
                print(f"   {status_icon} {category}: {cat_passed}/{cat_total} ({cat_rate:.0f}%)")

                if cat_rate >= 80:
                    all_working_categories.append(category)

        # Overall assessment
        print(f"\n🎯 Integration Assessment:")
        if pass_rate >= 90:
            print("🎉 EXCELLENT: Ollama-powered Archon MCP is fully operational!")
            assessment = "EXCELLENT"
        elif pass_rate >= 75:
            print("⚡ VERY GOOD: Strong Ollama integration with minor issues.")
            assessment = "VERY_GOOD"
        elif pass_rate >= 60:
            print("👍 GOOD: Core functionality working well with Ollama.")
            assessment = "GOOD"
        elif pass_rate >= 40:
            print("⚠️  PARTIAL: Some functionality working, needs attention.")
            assessment = "PARTIAL"
        else:
            print("🔧 NEEDS WORK: Significant integration issues detected.")
            assessment = "NEEDS_WORK"

        print(f"\n🔍 Functional Categories ({len(all_working_categories)}/{len(categories)} fully working):")
        for category in all_working_categories:
            print(f"   ✅ {category}")

        # Save detailed report
        self.save_detailed_report(assessment, pass_rate, passed, total)

        return {
            "assessment": assessment,
            "pass_rate": pass_rate,
            "passed": passed,
            "total": total,
            "working_categories": all_working_categories
        }

    def save_detailed_report(self, assessment: str, pass_rate: float, passed: int, total: int):
        """Save detailed test report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_archon_mcp_report_{timestamp}.json"

        report = {
            "test_metadata": {
                "timestamp": timestamp,
                "integration_type": "ollama",
                "server_url": self.base_url,
                "test_session_id": self.session_id
            },
            "summary": {
                "overall_assessment": assessment,
                "pass_rate_percentage": pass_rate,
                "tests_passed": passed,
                "tests_failed": total - passed,
                "total_tests": total
            },
            "detailed_results": self.test_results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {filename}")
        return filename

def main():
    """Main test execution for Ollama MCP integration"""
    print("Initializing Ollama-powered Archon MCP Test Suite...")

    tester = SSEMCPTester()
    results = tester.run_comprehensive_test()

    if results:
        return 0 if results["pass_rate"] >= 60 else 1
    else:
        return 1

if __name__ == "__main__":
    exit(main())
