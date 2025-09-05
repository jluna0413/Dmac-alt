#!/usr/bin/env python3
"""
Comprehensive MCP Session Debugging Utility

This script provides detailed debugging capabilities for MCP (Model Context Protocol) 
session management, protocol handshakes, and communication issues.

Features:
- Detailed MCP initialization debugging with full response analysis
- Session ID extraction and validation from multiple sources
- Protocol version compatibility        # Step 3: Tools endpoint testing
        tools_ok = False
        i        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        else:
            print(f"\n🎯 All systems operational - MCP session debugging complete!")

        return {esult:
            session_id = (init_result.get("result", {}).get("sessionId") or
                         init_result.get("sessionId"))
            tools_ok = self.test_tools_endpoint(session_id)

        # Generate summary and recommendations
- Network connectivity diagnostics
- SSE (Server-Sent Events) stream parsing
- Header analysis and validation
- Error diagnosis with actionable recommendations

Usage:
    # Basic debugging with default server
    python debug_mcp_session.py
    
    # Custom MCP server URL
    export MCP_SERVER_URL="http://your-server:8051/mcp"
    python debug_mcp_session.py
    
    # Enable verbose mode for detailed analysis
    export DEBUG_VERBOSE=true
    python debug_mcp_session.py

Exit Codes:
    0: Debugging completed successfully
    1: Critical connection or protocol errors detected
"""

import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

class MCPSessionDebugger:
    """
    Comprehensive MCP session debugging utility.
    
    This class provides detailed analysis of MCP protocol interactions,
    session management, and connectivity issues with actionable diagnostics.
    
    Attributes:
        base_url (str): The MCP server endpoint URL
        verbose (bool): Enable detailed logging and analysis
        session (requests.Session): HTTP session for consistent connections
        debug_results (List[Dict]): Accumulated debugging results
    """

    def __init__(self, base_url: Optional[str] = None, verbose: Optional[bool] = None):
        """
        Initialize the MCP session debugger.
        
        Args:
            base_url: MCP server URL (defaults to environment variable or localhost:8051)
            verbose: Enable verbose debugging (defaults to environment variable or False)
        """
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp")
        self.verbose = verbose if verbose is not None else os.getenv("DEBUG_VERBOSE", "false").lower() == "true"
        self.session = requests.Session()
        self.debug_results: List[Dict[str, Any]] = []

        # Configure session with proper MCP headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': 'MCP-Session-Debugger/1.0'
        })

    def log_debug(self, category: str, status: str, details: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log debugging information with structured data.
        
        Args:
            category: Debug category (e.g., "connectivity", "protocol", "session")
            status: Status indicator (e.g., "SUCCESS", "ERROR", "WARNING")
            details: Human-readable details
            data: Optional structured data for analysis
        """
        result = {
            "category": category,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.debug_results.append(result)
        
        # Console output with status emojis
        emoji = {
            "SUCCESS": "✅",
            "ERROR": "❌", 
            "WARNING": "⚠️",
            "INFO": "ℹ️"
        }.get(status, "🔍")

        print(f"{emoji} [{category.upper()}] {details}")

        if self.verbose and data:
            print(f"   📋 Data: {json.dumps(data, indent=6)}")

    def test_basic_connectivity(self) -> bool:
        """
        Test basic network connectivity to the MCP server.
        
        Returns:
            bool: True if basic connectivity is working, False otherwise
        """
        print("🔍 Testing Basic Network Connectivity...")

        try:
            # Simple HTTP GET to test reachability
            response = self.session.get(self.base_url.replace('/mcp', ''), timeout=5)

            self.log_debug(
                "connectivity", 
                "SUCCESS" if response.status_code < 500 else "WARNING",
                f"Server reachable - HTTP {response.status_code}",
                {"status_code": response.status_code, "response_size": len(response.content)}
            )
            return True

        except requests.ConnectionError as e:
            self.log_debug(
                "connectivity",
                "ERROR", 
                f"Connection failed: {str(e)[:100]}...",
                {"error_type": "ConnectionError", "error": str(e)}
            )
            return False
        except requests.Timeout as e:
            self.log_debug(
                "connectivity",
                "ERROR",
                f"Connection timeout: {str(e)}",
                {"error_type": "Timeout", "error": str(e)}
            )
            return False
        except (OSError, RuntimeError, ValueError) as e:
            self.log_debug(
                "connectivity",
                "ERROR",
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "error": str(e)}
            )
            return False

    def debug_mcp_initialize(self) -> Optional[Dict[str, Any]]:
        """
        Debug the MCP initialization process with comprehensive analysis.
        
        Returns:
            Optional[Dict]: Parsed initialization response or None if failed
        """
        print("\n🔍 Debugging MCP Protocol Initialization...")

        request_data = {
            "jsonrpc": "2.0",
            "id": f"debug-init-{int(time.time())}",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "MCP-Session-Debugger",
                    "version": "1.0.0"
                }
            }
        }

        self.log_debug(
            "protocol",
            "INFO",
            "Sending MCP initialize request",
            {"request": request_data}
        )

        try:
            response = self.session.post(self.base_url, json=request_data, timeout=10)

            # Log response details
            self.log_debug(
                "protocol",
                "SUCCESS" if response.status_code == 200 else "ERROR",
                f"Initialize response received - HTTP {response.status_code}",
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_type": response.headers.get('content-type', 'unknown'),
                    "response_size": len(response.content)
                }
            )

            # Analyze response format
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                return self._parse_sse_response(response.text)
            else:
                return self._parse_json_response(response.text)

        except (requests.RequestException, requests.Timeout) as e:
            self.log_debug(
                "protocol",
                "ERROR",
                f"Initialize request failed: {str(e)}",
                {"error_type": type(e).__name__, "error": str(e)}
            )
            return None

    def _parse_sse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse Server-Sent Events response format.
        
        Args:
            response_text: Raw SSE response text
            
        Returns:
            Optional[Dict]: Parsed response data or None if parsing failed
        """
        self.log_debug("protocol", "INFO", "Parsing SSE response format")

        lines = response_text.strip().split('\n')
        parsed_data = None

        for i, line in enumerate(lines):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    parsed_data = data

                    self.log_debug(
                        "protocol",
                        "SUCCESS",
                        f"Successfully parsed SSE data line {i+1}",
                        {"parsed_data": data}
                    )

                    # Analyze session information
                    self._analyze_session_data(data)

                except json.JSONDecodeError as e:
                    self.log_debug(
                        "protocol",
                        "ERROR",
                        f"JSON parse error in SSE line {i+1}: {str(e)}",
                        {"line_content": line, "error": str(e)}
                    )
            elif line.strip():
                self.log_debug(
                    "protocol",
                    "INFO",
                    f"SSE metadata line {i+1}: {line}"
                )

        return parsed_data

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse standard JSON response format.
        
        Args:
            response_text: Raw JSON response text
            
        Returns:
            Optional[Dict]: Parsed response data or None if parsing failed
        """
        self.log_debug("protocol", "INFO", "Parsing JSON response format")

        try:
            data = json.loads(response_text)

            self.log_debug(
                "protocol",
                "SUCCESS",
                "Successfully parsed JSON response",
                {"parsed_data": data}
            )

            # Analyze session information
            self._analyze_session_data(data)
            return data

        except json.JSONDecodeError as e:
            self.log_debug(
                "protocol",
                "ERROR",
                f"JSON parse error: {str(e)}",
                {"response_text": response_text[:200] + "..." if len(response_text) > 200 else response_text}
            )
            return None

    def _analyze_session_data(self, data: Dict[str, Any]) -> None:
        """
        Analyze session-related information in the response.
        
        Args:
            data: Parsed response data
        """
        # Check for session ID in various locations
        session_sources = [
            ("result.sessionId", data.get("result", {}).get("sessionId")),
            ("sessionId", data.get("sessionId")),
            ("id", data.get("id"))
        ]

        session_found = False
        for source, session_id in session_sources:
            if session_id:
                self.log_debug(
                    "session",
                    "SUCCESS",
                    f"Session ID found in {source}: {session_id}",
                    {"session_id": session_id, "source": source}
                )
                session_found = True

        if not session_found:
            self.log_debug(
                "session",
                "WARNING",
                "No session ID found in response",
                {"available_fields": list(data.keys())}
            )

        # Analyze capabilities
        capabilities = data.get("result", {}).get("capabilities", {})
        if capabilities:
            self.log_debug(
                "protocol",
                "SUCCESS",
                f"Server capabilities detected: {list(capabilities.keys())}",
                {"capabilities": capabilities}
            )

    def test_tools_endpoint(self, session_id: Optional[str] = None) -> bool:
        """
        Test the tools/list endpoint with session management.
        
        Args:
            session_id: Optional session ID to use
            
        Returns:
            bool: True if tools endpoint is accessible, False otherwise
        """
        print("\n🔍 Testing Tools Endpoint Access...")

        request_data: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": f"debug-tools-{int(time.time())}",
            "method": "tools/list"
        }

        # Add session ID if provided
        if session_id:
            request_data["params"] = {"sessionId": session_id}

        try:
            response = self.session.post(self.base_url, json=request_data, timeout=10)

            success = response.status_code == 200
            self.log_debug(
                "tools",
                "SUCCESS" if success else "ERROR",
                f"Tools endpoint response - HTTP {response.status_code}",
                {
                    "status_code": response.status_code,
                    "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
                }
            )

            return success

        except (requests.RequestException, requests.Timeout) as e:
            self.log_debug(
                "tools",
                "ERROR",
                f"Tools endpoint failed: {str(e)}",
                {"error_type": type(e).__name__, "error": str(e)}
            )
            return False

    def run_comprehensive_debug(self) -> Dict[str, Any]:
        """
        Run comprehensive debugging session with full analysis.
        
        Returns:
            Dict containing debug summary and recommendations
        """
        print("🚀 MCP SESSION COMPREHENSIVE DEBUG ANALYSIS")
        print(f"📡 Target Server: {self.base_url}")
        print(f"🔍 Verbose Mode: {'Enabled' if self.verbose else 'Disabled'}")
        print("=" * 70)        # Step 1: Basic connectivity
        connectivity_ok = self.test_basic_connectivity()

        # Step 2: MCP protocol initialization
        init_result = None
        if connectivity_ok:
            init_result = self.debug_mcp_initialize()

        # Step 3: Tools endpoint testing
        tools_ok = False
        if init_result:
            session_id = (init_result.get("result", {}).get("sessionId") or
                         init_result.get("sessionId"))
            tools_ok = self.test_tools_endpoint(session_id)

        # Generate summary and recommendations
        return self._generate_debug_summary(connectivity_ok, init_result is not None, tools_ok)

    def _generate_debug_summary(self, connectivity_ok: bool, init_ok: bool, tools_ok: bool) -> Dict[str, Any]:
        """
        Generate comprehensive debug summary with recommendations.

        Args:
            connectivity_ok: Whether basic connectivity succeeded
            init_ok: Whether MCP initialization succeeded
            tools_ok: Whether tools endpoint access succeeded

        Returns:
            Dict containing summary and recommendations
        """
        print("\n" + "=" * 70)
        print("📊 DEBUG ANALYSIS SUMMARY")
        print("=" * 70)        # Calculate overall health
        checks = [connectivity_ok, init_ok, tools_ok]
        health_score = sum(checks) / len(checks) * 100

        # Determine overall status
        if health_score >= 100:
            status = "EXCELLENT"
            emoji = "🎉"
        elif health_score >= 66:
            status = "GOOD"
            emoji = "✅"
        elif health_score >= 33:
            status = "PARTIAL"
            emoji = "⚠️"
        else:
            status = "CRITICAL"
            emoji = "❌"
        
        print(f"{emoji} Overall Status: {status} ({health_score:.0f}%)")
        print(f"🔗 Basic Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
        print(f"🤝 MCP Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
        print(f"🛠️  Tools Endpoint: {'✅ PASS' if tools_ok else '❌ FAIL'}")

        # Generate recommendations
        recommendations = []
        if not connectivity_ok:
            recommendations.extend([
                "• Verify MCP server is running and accessible",
                "• Check network connectivity and firewall settings",
                "• Confirm server URL is correct"
            ])
        if not init_ok:
            recommendations.extend([
                "• Verify MCP protocol version compatibility",
                "• Check server-side initialization handling",
                "• Review request/response format requirements"
            ])
        if not tools_ok:
            recommendations.extend([
                "• Verify session management implementation",
                "• Check tools endpoint availability",
                "• Review session ID handling"
            ])

        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        else:
            print(f"\n🎯 All systems operational - MCP session debugging complete!")

        return {
            "status": status,
            "health_score": health_score,
            "connectivity": connectivity_ok,
            "initialization": init_ok,
            "tools_access": tools_ok,
            "recommendations": recommendations,
            "debug_results": self.debug_results
        }

    def save_debug_report(self, summary: Dict[str, Any]) -> str:
        """
        Save comprehensive debug report to file.
        
        Args:
            summary: Debug summary from run_comprehensive_debug
            
        Returns:
            str: Filename of saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mcp_debug_report_{timestamp}.json"

        report = {
            "debug_session": {
                "timestamp": timestamp,
                "server_url": self.base_url,
                "verbose_mode": self.verbose,
                "overall_status": summary["status"],
                "health_score": summary["health_score"]
            },
            "test_results": {
                "connectivity": summary["connectivity"],
                "initialization": summary["initialization"], 
                "tools_access": summary["tools_access"]
            },
            "recommendations": summary["recommendations"],
            "detailed_logs": summary["debug_results"]
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Debug report saved to: {filename}")
            return filename
        except OSError as e:
            print(f"⚠️ Failed to save debug report: {e}")
            return ""


def main() -> int:
    """
    Main debugging execution with comprehensive error handling.
    
    Returns:
        int: Exit code (0 for success, 1 for critical issues detected)
    """
    print("Starting MCP Session Debug Analysis...")

    try:
        debugger = MCPSessionDebugger()
        summary = debugger.run_comprehensive_debug()

        if summary:
            debugger.save_debug_report(summary)
            # Return success if at least basic connectivity works
            return 0 if summary["health_score"] >= 33 else 1
        else:
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Debug session interrupted by user")
        return 1
    except (OSError, RuntimeError, ValueError) as e:
        print(f"❌ Unexpected error during debugging: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
