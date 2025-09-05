#!/usr/bin/env python3
"""
Simple MCP Client Test for Ollama-Powered Archon.

This script uses the official MCP Python client over SSE. It supports both
newer (sse_client) and older (sse_connect) helper names.

Features:
- Automatic MCP library installation if missing
- Comprehensive error handling with specific exception types
- JSON result logging with timestamps
- Graceful connection management with proper cleanup

Usage:
    python test_mcp_client.py

Environment Variables:
    MCP_SERVER_URL: Base URL for the MCP server (default: http://localhost:8051/mcp)
"""

import asyncio
import importlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _resolve_mcp_client() -> Tuple[Any, Optional[Any]]:
    """
    Resolve MCP client dependencies and return ClientSession and SSE connection function.

    Returns:
        Tuple containing:
        - ClientSession class from MCP library
        - SSE connection function (sse_client or sse_connect)

    Raises:
        ImportError: If MCP library cannot be imported or installed
        AttributeError: If required SSE functions are not available
    """
    try:
        from mcp import ClientSession as _ClientSession  # type: ignore
    except ImportError:
        # Allow runtime install for convenience
        print("❌ MCP client library not available. Installing...")
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp"])  # noqa: S603,S607
        from mcp import ClientSession as _ClientSession  # type: ignore

    sse_open = None
    try:
        sse_mod = importlib.import_module("mcp.client.sse")
        sse_open = getattr(sse_mod, "sse_client", None) or getattr(sse_mod, "sse_connect", None)
    except ModuleNotFoundError:
        sse_open = None
    return _ClientSession, sse_open


MCPClientSession, _SSE_OPEN = _resolve_mcp_client()


class ArchonMCPClientTester:
    """
    Test suite for Archon MCP server functionality using official MCP Python client.

    This class provides comprehensive testing of MCP tools through SSE connections,
    with automatic connection management and detailed result logging.

    Attributes:
        base_url: Base URL for MCP server endpoint
        session: Active MCP client session (None when disconnected)
        test_results: List of test results with timestamps and details
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Initialize the MCP client tester.

        Args:
            base_url: MCP server base URL. If None, uses environment variable
                     MCP_SERVER_URL or defaults to http://localhost:8051/mcp
        """
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp")
        self.session: Optional[Any] = None
        self._sse_cm: Optional[Any] = None
        self._streams: Optional[Tuple[Any, Any]] = None
        self.test_results: List[Dict[str, Any]] = []
        logger.info("Initialized MCP client tester for %s", self.base_url)

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current MCP client configuration.

        Returns:
            Dictionary with configuration status and details
        """
        config_status = {
            "base_url": self.base_url,
            "mcp_client_available": MCPClientSession is not None,
            "sse_transport_available": _SSE_OPEN is not None,
            "valid": True,
            "issues": []
        }

        if not MCPClientSession:
            config_status["valid"] = False
            config_status["issues"].append("MCP ClientSession not available")

        if not _SSE_OPEN:
            config_status["valid"] = False
            config_status["issues"].append("SSE transport not available")

        return config_status

    def log_test(self, tool_name: str, success: bool, details: str = "") -> None:
        """
        Log a test result with timestamp and status.

        Args:
            tool_name: Name of the MCP tool being tested
            success: Whether the test passed or failed
            details: Additional details about the test execution
        """
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "tool": tool_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)
        print(f"{status} {tool_name}: {details}")

    async def connect(self) -> bool:
        """
        Establish connection to MCP server using SSE transport.

        Returns:
            True if connection successful, False otherwise

        Raises:
            RuntimeError: If MCP SSE client is not available
        """
        try:
            if _SSE_OPEN is None:
                raise RuntimeError(
                    "mcp.client.sse.sse_client/sse_connect not available. Please upgrade the 'mcp' package."
                )

            # Open SSE connection -> (read, write)
            open_fn: Any = cast(Any, _SSE_OPEN)
            self._sse_cm = open_fn(self.base_url)
            streams = await cast(Any, self._sse_cm).__aenter__()
            read, write = streams
            self._streams = (read, write)

            # Create session from streams
            session_ctor: Any = cast(Any, MCPClientSession)
            self.session = session_ctor(read, write)
            await cast(Any, self.session).__aenter__()

            # Connectivity test
            tools = await cast(Any, self.session).list_tools()
            print(f"🔗 Connected. Tools available: {len(tools.tools)}")
            for tool in tools.tools:
                name = getattr(tool, "name", "<tool>")
                desc = getattr(tool, "description", "")
                print(f"   - {name}: {desc}")
            return True
        except (OSError, RuntimeError, AttributeError, ConnectionError, TimeoutError, ValueError) as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False

    async def disconnect(self) -> None:
        try:
            if self.session is not None:
                await self.session.__aexit__(None, None, None)
                self.session = None
            if self._sse_cm is not None:
                await self._sse_cm.__aexit__(None, None, None)
                self._sse_cm = None
        except (OSError, RuntimeError, AttributeError) as e:
            print(f"Warning: Error during disconnect: {e}")

    async def test_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """
        Test a specific MCP tool with given arguments.

        Args:
            tool_name: Name of the MCP tool to test
            arguments: Optional dictionary of arguments to pass to the tool

        Returns:
            True if tool execution succeeded, False otherwise
        """
        if arguments is None:
            arguments = {}
        try:
            if self.session is None:
                self.log_test(tool_name, False, "Not connected")
                return False
            result = await self.session.call_tool(tool_name, arguments)
            if getattr(result, "isError", False):
                self.log_test(tool_name, False, f"Tool error: {result.content}")
                return False
            content = str(getattr(result, "content", ""))
            self.log_test(tool_name, True, f"Response: {content[:100] + ('...' if len(content) > 100 else '')}")
            return True
        except (OSError, RuntimeError, AttributeError, TypeError, ValueError) as e:
            self.log_test(tool_name, False, f"Exception: {e}")
            return False

    async def run_basic_tests(self) -> bool:
        """
        Execute a comprehensive suite of basic MCP tool tests.

        This method tests core functionality across different categories:
        - Health and system status tools
        - RAG and knowledge base tools
        - Project management tools

        Returns:
            True if all tests passed, False if any test failed
        """
        print("🚀 Starting Basic MCP Tools Test with Ollama Integration")
        print("=" * 70)
        if not await self.connect():
            return False
        try:
            print("\n🏥 Health & System Tests:")
            await self.test_tool("health_check")
            await self.test_tool("session_info")

            print("\n🔍 RAG & Knowledge Tests:")
            await self.test_tool("get_available_sources")
            await self.test_tool("perform_rag_query", {"query": "What is MCP protocol?", "match_count": 3})
            await self.test_tool("search_code_examples", {"query": "FastAPI endpoint", "match_count": 3})

            print("\n📊 Project Management Tests:")
            await self.test_tool("list_projects")
            await self.test_tool("list_tasks")
            await self.test_tool("list_documents")

            print("\n" + "=" * 70)
            print("📋 TEST RESULTS SUMMARY")
            print("=" * 70)
            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)
            pass_rate = (passed / total) * 100 if total > 0 else 0
            print(f"✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
            print(f"❌ Failed: {total - passed}/{total}")
            return passed == total
        finally:
            await self.disconnect()


async def main() -> int:
    """
    Main entry point for MCP client testing.

    Returns:
        0 if all tests passed, 1 if any test failed or configuration invalid
    """
    print("🚀 Starting Archon MCP Client Test Suite")
    print("=" * 50)

    tester = ArchonMCPClientTester()

    # Validate configuration first
    config = tester.validate_configuration()
    print("📋 Configuration Status:")
    print(f"   Base URL: {config['base_url']}")
    print(f"   MCP Client: {'✅' if config['mcp_client_available'] else '❌'}")
    print(f"   SSE Transport: {'✅' if config['sse_transport_available'] else '❌'}")

    if not config["valid"]:
        print(f"❌ Configuration invalid: {', '.join(config['issues'])}")
        return 1

    print("✅ Configuration valid, proceeding with tests...\n")

    try:
        success = await tester.run_basic_tests()

        # Generate detailed results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"mcp_basic_test_results_{ts}.json"

        detailed_results = {
            "success": success,
            "configuration": config,
            "results": tester.test_results,
            "timestamp": ts,
            "summary": {
                "total": len(tester.test_results),
                "passed": sum(1 for r in tester.test_results if r["success"]),
                "failed": sum(1 for r in tester.test_results if not r["success"]),
            },
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        return 130  # Standard exit code for SIGINT
    except (
        OSError,
        RuntimeError,
        AttributeError,
        ConnectionError,
        TimeoutError,
        ValueError,
        TypeError,
    ) as e:
        logger.exception("Unexpected error during test execution")
        print(f"💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
