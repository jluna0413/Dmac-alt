#!/usr/bin/env python3
"""
Master MCP Test Suite Runner

This script orchestrates the execution of all MCP test files with comprehensive
reporting and analysis. It provides a unified interface for running the complete
test suite and generates consolidated reports.

Features:
- Sequential execution of all test scripts
- Consolidated test reporting with pass/fail statistics
- Environment validation and setup checks
- Comprehensive error handling and recovery
- Detailed execution timing and performance metrics
- Support for selective test execution

Usage:
    # Run all tests with default configuration
    python run_all_tests.py
    
    # Run specific test categories
    python run_all_tests.py --category basic
    python run_all_tests.py --category advanced
    python run_all_tests.py --category debug
    
    # Custom MCP server URL
    export MCP_SERVER_URL="http://your-server:8051/mcp"
    python run_all_tests.py
    
    # Enable verbose logging for all tests
    export DEBUG_VERBOSE=true
    python run_all_tests.py

Test Categories:
- basic: Core functionality tests (test_mcp_client.py, test_mcp_direct.py)
- advanced: Comprehensive tool testing (test_archon_mcp_tools.py, test_ollama_mcp.py)
- session: Session management tests (test_session_methods.py)
- debug: Debugging and diagnostics (debug_mcp_session.py)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class MCPTestSuiteRunner:
    """
    Master test suite runner for all MCP testing utilities.
    
    This class coordinates the execution of multiple test scripts,
    collects results, and generates comprehensive reports.
    
    Attributes:
        base_path (Path): Base directory containing test files
        results (List[Dict]): Accumulated test execution results
        verbose (bool): Enable verbose logging
    """
    
    def __init__(self, base_path: Optional[str] = None, verbose: bool = False):
        """
        Initialize the test suite runner.
        
        Args:
            base_path: Directory containing test files (defaults to current directory)
            verbose: Enable verbose logging
        """
        self.base_path = Path(base_path or os.getcwd())
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
        
        # Define test configurations
        self.test_configs = {
            "basic": [
                {
                    "name": "MCP Client Test",
                    "script": "test_mcp_client.py",
                    "description": "Official MCP Python client testing with SSE transport",
                    "timeout": 60
                },
                {
                    "name": "MCP Direct Test", 
                    "script": "test_mcp_direct.py",
                    "description": "Direct HTTP JSON-RPC testing for MCP endpoints",
                    "timeout": 45
                }
            ],
            "advanced": [
                {
                    "name": "Archon MCP Tools Test",
                    "script": "test_archon_mcp_tools.py", 
                    "description": "Comprehensive MCP tools validation suite",
                    "timeout": 90
                },
                {
                    "name": "Ollama MCP Test",
                    "script": "test_ollama_mcp.py",
                    "description": "Ollama-powered Archon integration testing", 
                    "timeout": 120
                }
            ],
            "session": [
                {
                    "name": "Session Methods Test",
                    "script": "test_session_methods.py",
                    "description": "MCP session management validation",
                    "timeout": 30
                }
            ],
            "debug": [
                {
                    "name": "MCP Session Debug",
                    "script": "debug_mcp_session.py",
                    "description": "Comprehensive MCP debugging and diagnostics",
                    "timeout": 45
                }
            ]
        }

    def validate_environment(self) -> Tuple[bool, List[str]]:
        """
        Validate the testing environment and dependencies.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append(f"Python 3.8+ required, found {sys.version}")
        
        # Check required test files exist
        for tests in self.test_configs.values():
            for test in tests:
                script_path = self.base_path / test["script"]
                if not script_path.exists():
                    issues.append(f"Missing test script: {test['script']}")
        
        # Check MCP server configuration
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp")
        if not mcp_url.startswith(("http://", "https://")):
            issues.append(f"Invalid MCP_SERVER_URL format: {mcp_url}")
        
        return len(issues) == 0, issues

    def run_test_script(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test script and collect results.
        
        Args:
            test_config: Test configuration dictionary
            
        Returns:
            Dict containing execution results
        """
        script_path = self.base_path / test_config["script"]
        start_time = time.time()
        
        self._print_test_header(test_config)
        
        try:
            result = self._execute_script(script_path, test_config)
            execution_time = time.time() - start_time
            test_result = self._create_success_result(test_config, result, execution_time)
            self._print_completion_status(test_result, result)
            return test_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return self._create_timeout_result(test_config, execution_time)
            
        except (OSError, ValueError) as e:
            execution_time = time.time() - start_time
            return self._create_error_result(test_config, execution_time, e)

    def _print_test_header(self, test_config: Dict[str, Any]) -> None:
        """Print test execution header."""
        print(f"\n🧪 Running {test_config['name']}...")
        print(f"📄 Script: {test_config['script']}")
        print(f"📝 Description: {test_config['description']}")

    def _execute_script(self, script_path: Path, test_config: Dict[str, Any]) -> subprocess.CompletedProcess:
        """Execute the test script."""
        return subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=test_config.get("timeout", 60),
            cwd=str(self.base_path),
            check=False
        )

    def _create_success_result(self, test_config: Dict[str, Any], 
                              result: subprocess.CompletedProcess, 
                              execution_time: float) -> Dict[str, Any]:
        """Create result dictionary for successful execution."""
        success = result.returncode == 0
        status = "✅ PASS" if success else "❌ FAIL"
        
        test_result = {
            "name": test_config["name"],
            "script": test_config["script"],
            "status": status,
            "success": success,
            "exit_code": result.returncode,
            "execution_time": execution_time,
            "stdout_lines": len(result.stdout.splitlines()),
            "stderr_lines": len(result.stderr.splitlines()),
            "timestamp": datetime.now().isoformat()
        }
        
        # Include output based on verbose mode
        if self.verbose:
            test_result.update({
                "stdout": result.stdout,
                "stderr": result.stderr
            })
        else:
            test_result.update({
                "stdout_preview": self._truncate_output(result.stdout),
                "stderr_preview": self._truncate_output(result.stderr)
            })
        
        return test_result

    def _truncate_output(self, output: str, max_length: int = 200) -> str:
        """Truncate output to specified length."""
        return output[:max_length] + "..." if len(output) > max_length else output

    def _print_completion_status(self, test_result: Dict[str, Any], 
                                result: subprocess.CompletedProcess) -> None:
        """Print test completion status."""
        print(f"{test_result['status']} Completed in {test_result['execution_time']:.1f}s")
        
        if not test_result['success']:
            print(f"⚠️ Exit code: {result.returncode}")
            if result.stderr:
                print(f"❌ Error output: {result.stderr[:100]}...")

    def _create_timeout_result(self, test_config: Dict[str, Any], 
                              execution_time: float) -> Dict[str, Any]:
        """Create result for timed out execution."""
        test_result = {
            "name": test_config["name"],
            "script": test_config["script"],
            "status": "⏰ TIMEOUT",
            "success": False,
            "exit_code": -1,
            "execution_time": execution_time,
            "error": f"Test timed out after {test_config.get('timeout', 60)}s",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"⏰ TIMEOUT after {execution_time:.1f}s")
        return test_result

    def _create_error_result(self, test_config: Dict[str, Any], 
                            execution_time: float, error: Exception) -> Dict[str, Any]:
        """Create result for execution errors."""
        test_result = {
            "name": test_config["name"],
            "script": test_config["script"],
            "status": "💥 ERROR",
            "success": False,
            "exit_code": -2,
            "execution_time": execution_time,
            "error": f"Execution error: {str(error)}",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"💥 ERROR: {str(error)}")
        return test_result

    def run_test_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Run all tests in a specific category.
        
        Args:
            category: Test category name
            
        Returns:
            List of test results
        """
        if category not in self.test_configs:
            print(f"❌ Unknown test category: {category}")
            return []
        
        tests = self.test_configs[category]
        category_results = []
        
        print(f"\n🚀 Running {category.upper()} test category ({len(tests)} tests)")
        print("=" * 60)
        
        for test_config in tests:
            result = self.run_test_script(test_config)
            category_results.append(result)
            self.results.append(result)
        
        return category_results

    def run_all_tests(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run all test categories or specified categories.
        
        Args:
            categories: List of categories to run (defaults to all)
            
        Returns:
            Dict containing comprehensive test summary
        """
        if categories is None:
            categories = list(self.test_configs.keys())
        
        print("🚀 MCP COMPREHENSIVE TEST SUITE")
        print(f"📡 Server: {os.getenv('MCP_SERVER_URL', 'http://localhost:8051/mcp')}")
        print(f"🔍 Verbose: {'Enabled' if self.verbose else 'Disabled'}")
        print(f"📋 Categories: {', '.join(categories)}")
        print("=" * 70)
        
        # Validate environment first
        env_valid, env_issues = self.validate_environment()
        if not env_valid:
            print("❌ Environment validation failed:")
            for issue in env_issues:
                print(f"   • {issue}")
            return {"status": "ENVIRONMENT_ERROR", "issues": env_issues}
        
        print("✅ Environment validation passed")
        
        # Run tests by category
        start_time = time.time()
        for category in categories:
            self.run_test_category(category)
        
        total_time = time.time() - start_time
        
        # Generate summary
        return self._generate_test_summary(total_time)

    def _generate_test_summary(self, total_time: float) -> Dict[str, Any]:
        """
        Generate comprehensive test summary and statistics.
        
        Args:
            total_time: Total execution time in seconds
            
        Returns:
            Dict containing summary statistics and recommendations
        """
        self._print_summary_header()
        stats = self._calculate_test_statistics(total_time)
        
        self._print_all_summary_sections(stats)
        assessment = self._determine_overall_status(stats["pass_rate"])
        self._print_overall_assessment(assessment)
        
        return self._create_summary_dict(stats, assessment)

    def _print_all_summary_sections(self, stats: Dict[str, Any]) -> None:
        """Print all summary sections."""
        self._print_test_statistics(stats)
        self._print_category_breakdown()
        self._print_failed_tests(stats["failed_tests"])

    def _print_summary_header(self) -> None:
        """Print the summary section header."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 70)

    def _calculate_test_statistics(self, total_time: float) -> Dict[str, Any]:
        """Calculate basic test statistics."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": pass_rate,
            "total_time": total_time
        }

    def _print_test_statistics(self, stats: Dict[str, Any]) -> None:
        """Print basic test statistics."""
        print(f"✅ Passed: {stats['passed_tests']}/{stats['total_tests']} ({stats['pass_rate']:.1f}%)")
        print(f"❌ Failed: {stats['failed_tests']}/{stats['total_tests']}")
        print(f"⏱️  Total Time: {stats['total_time']:.1f}s")
        if stats['total_tests'] > 0:
            avg_time = stats['total_time'] / stats['total_tests']
            print(f"⚡ Average Time: {avg_time:.1f}s per test")

    def _print_category_breakdown(self) -> None:
        """Print results breakdown by category."""
        print(f"\n📈 Results by Category:")
        for category, tests in self.test_configs.items():
            category_results = [r for r in self.results if r["script"] in [t["script"] for t in tests]]
            if category_results:
                cat_passed = sum(1 for r in category_results if r["success"])
                cat_total = len(category_results)
                print(f"   {category.upper()}: {cat_passed}/{cat_total} passed")

    def _print_failed_tests(self, failed_count: int) -> None:
        """Print details of failed tests."""
        if failed_count > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['name']}: {result.get('error', 'See logs for details')}")

    def _determine_overall_status(self, pass_rate: float) -> Dict[str, str]:
        """Determine overall test status assessment."""
        if pass_rate >= 90:
            return {"status": "EXCELLENT", "emoji": "🎉", "message": "All systems operational!"}
        elif pass_rate >= 70:
            return {"status": "GOOD", "emoji": "✅", "message": "Most functionality working correctly."}
        elif pass_rate >= 50:
            return {"status": "PARTIAL", "emoji": "⚠️", "message": "Core functions work, some issues detected."}
        else:
            return {"status": "CRITICAL", "emoji": "❌", "message": "Significant issues detected - review failed tests."}

    def _print_overall_assessment(self, assessment: Dict[str, str]) -> None:
        """Print the overall assessment."""
        print(f"\n{assessment['emoji']} Overall Status: {assessment['status']}")
        print(f"💡 {assessment['message']}")

    def _create_summary_dict(self, stats: Dict[str, Any], assessment: Dict[str, str]) -> Dict[str, Any]:
        """Create the final summary dictionary."""
        return {
            "status": assessment["status"],
            "pass_rate": stats["pass_rate"],
            "total_tests": stats["total_tests"],
            "passed_tests": stats["passed_tests"],
            "failed_tests": stats["failed_tests"],
            "total_time": stats["total_time"],
            "detailed_results": self.results
        }

    def save_comprehensive_report(self, summary: Dict[str, Any]) -> str:
        """
        Save comprehensive test report to JSON file.
        
        Args:
            summary: Test summary from run_all_tests
            
        Returns:
            str: Filename of saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mcp_test_suite_report_{timestamp}.json"
        
        report = {
            "test_suite_summary": {
                "timestamp": timestamp,
                "server_url": os.getenv("MCP_SERVER_URL", "http://localhost:8051/mcp"),
                "overall_status": summary["status"],
                "pass_rate": summary["pass_rate"],
                "execution_time": summary["total_time"],
                "total_tests": summary["total_tests"],
                "passed_tests": summary["passed_tests"],
                "failed_tests": summary["failed_tests"]
            },
            "test_configurations": self.test_configs,
            "detailed_results": summary["detailed_results"]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Comprehensive report saved to: {filename}")
            return filename
        except OSError as e:
            print(f"⚠️ Failed to save report: {e}")
            return ""


def main() -> int:
    """
    Main execution with command-line argument parsing.
    
    Returns:
        int: Exit code (0 for success, 1 for failures detected)
    """
    parser = argparse.ArgumentParser(
        description="MCP Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests
  python run_all_tests.py --category basic   # Run basic tests only
  python run_all_tests.py --verbose          # Enable verbose output
        """
    )
    
    parser.add_argument(
        "--category",
        choices=["basic", "advanced", "session", "debug"],
        help="Run specific test category only"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with full test logs"
    )
    
    parser.add_argument(
        "--base-path",
        help="Base directory containing test files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        runner = MCPTestSuiteRunner(
            base_path=args.base_path,
            verbose=args.verbose or os.getenv("DEBUG_VERBOSE", "false").lower() == "true"
        )
        
        categories = [args.category] if args.category else None
        summary = runner.run_all_tests(categories)
        
        if summary.get("status") != "ENVIRONMENT_ERROR":
            runner.save_comprehensive_report(summary)
            return 0 if summary["pass_rate"] >= 50 else 1
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        return 1
    except (OSError, SystemError, RuntimeError) as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
