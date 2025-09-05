# Archon MCP Test Suite

A comprehensive testing framework for the Archon Model Control Protocol (MCP) server, designed to validate MCP tool functionality with Ollama integration.

## Overview

This test suite provides both HTTP JSON-RPC and native MCP client testing capabilities to ensure your Archon MCP server is working correctly with all supported tools and integrations.

## Test Files

### Master Test Suite

- **`run_all_tests.py`** - Master test runner executing all test categories with comprehensive reporting
- **`mcp_config.py`** - Configuration management utility for consistent test settings

### Core Test Scripts

- **`test_mcp_client.py`** - Official MCP Python client test using SSE transport
- **`test_mcp_direct.py`** - Direct HTTP JSON-RPC testing for MCP endpoints
- **`test_archon_mcp_tools.py`** - Comprehensive tool validation suite

### Specialized Test Scripts

- **`debug_mcp_session.py`** - Comprehensive session debugging and diagnostics utility
- **`test_session_methods.py`** - Session management validation with multiple approaches
- **`test_tools_params.py`** - Parameter validation for MCP tools
- **`test_ollama_*.py`** - Ollama integration testing variants

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure your Archon MCP server is running
# Default: http://localhost:8051/mcp
```

### Configuration Management

```bash
# Validate current configuration
python mcp_config.py validate

# Show current configuration
python mcp_config.py show

# Set custom MCP server URL
python mcp_config.py set mcp_server.url "http://your-server:8051/mcp"

# Test connectivity
python mcp_config.py test-connection

# Generate default configuration file
python mcp_config.py generate-config
```

### Basic Usage

```bash
# Run all tests with master test runner
python run_all_tests.py

# Run specific test categories
python run_all_tests.py --category basic
python run_all_tests.py --category advanced

# Run individual test scripts
python test_mcp_client.py
python test_mcp_direct.py
python test_archon_mcp_tools.py

# Debug session issues
python debug_mcp_session.py
```

### Environment Configuration

```bash
# Set custom MCP server URL
export MCP_SERVER_URL="http://your-server:8051/mcp"

# Enable debug logging
export LOG_LEVEL="DEBUG"

# Set custom session ID for testing
export TEST_SESSION_ID="your-session-id"
```

## Test Categories

### 🏥 Health & System Tests
- `health_check` - Server health validation
- `session_info` - Session status and metadata

### 🔍 RAG & Knowledge Base Tests  
- `get_available_sources` - List available knowledge sources
- `perform_rag_query` - Test RAG query functionality
- `search_code_examples` - Code search capabilities

### 📊 Project Management Tests
- `list_projects` - Project listing
- `create_project` - Project creation
- `get_project` - Project retrieval
- `list_tasks` - Task management
- `create_task` - Task creation
- `list_documents` - Document listing
- `create_document` - Document creation
- `list_versions` - Version control
- `get_project_features` - Feature tracking

## Output and Logging

### Test Results

Each test run generates:
- Console output with real-time status
- Detailed JSON results file with timestamp
- Pass/fail summary with statistics

### Sample Output

```
🚀 Starting Archon MCP Client Test Suite
==================================================
📋 Configuration Status:
   Base URL: http://localhost:8051/mcp
   MCP Client: ✅
   SSE Transport: ✅
✅ Configuration valid, proceeding with tests...

🏥 Health & System Tests:
✅ PASS health_check: Response: {"health": "ok", "uptime": 3600}
✅ PASS session_info: Response: {"session_id": "abc123", "tools": 14}

📋 TEST RESULTS SUMMARY
======================================
✅ Passed: 10/10 (100.0%)
❌ Failed: 0/10

📄 Detailed results saved to: mcp_basic_test_results_20250904_143022.json
```

### JSON Results Format

```json
{
  "success": true,
  "configuration": {
    "base_url": "http://localhost:8051/mcp",
    "mcp_client_available": true,
    "sse_transport_available": true,
    "valid": true,
    "issues": []
  },
  "results": [
    {
      "tool": "health_check",
      "status": "✅ PASS", 
      "success": true,
      "details": "Response: {\"health\": \"ok\"}",
      "timestamp": "2025-09-04T14:30:22.123456"
    }
  ],
  "summary": {
    "total": 10,
    "passed": 10,
    "failed": 0
  }
}
```

## Troubleshooting

### Common Issues

**Connection Refused**
```
❌ Failed to connect to MCP server: Connection refused
```
- Verify Archon MCP server is running
- Check the base URL configuration
- Ensure port 8051 is accessible

**MCP Client Not Available**
```
❌ Configuration invalid: MCP ClientSession not available
```
- Install MCP client: `pip install mcp`
- Verify Python environment

**SSE Transport Issues**
```
❌ Configuration invalid: SSE transport not available
```
- Upgrade MCP package: `pip install --upgrade mcp`
- Check for newer client versions

**Tool Not Found**
```
❌ FAIL tool_name: Tool error: Tool not found
```
- Verify tool is registered in MCP server
- Check tool name spelling
- Confirm server supports the requested tool

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python test_mcp_client.py
```

### Manual Testing

For individual tool testing:

```python
from test_mcp_client import ArchonMCPClientTester

async def test_single_tool():
    tester = ArchonMCPClientTester()
    if await tester.connect():
        await tester.test_tool("health_check")
        await tester.disconnect()

# Run with: python -c "import asyncio; asyncio.run(test_single_tool())"
```

## Best Practices

### Test Development

1. **Specific Exception Handling** - Use specific exception types instead of broad `except Exception:`
2. **Proper Resource Cleanup** - Always disconnect MCP sessions in `finally` blocks
3. **Detailed Logging** - Include context and error details in test results
4. **Configurable Endpoints** - Support environment variables for flexible testing

### Performance

1. **Connection Reuse** - Maintain single connection for multiple tool tests
2. **Parallel Testing** - Use async capabilities for concurrent tool validation
3. **Timeout Management** - Set appropriate timeouts for network operations

### Error Recovery

1. **Graceful Degradation** - Continue testing other tools if one fails
2. **Retry Logic** - Implement retry for transient network issues
3. **Clear Error Messages** - Provide actionable error information

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: MCP Test Suite
on: [push, pull_request]

jobs:
  test-mcp:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Start Archon MCP Server
      run: |
        python -m archon.mcp_server &
        sleep 10
    - name: Run MCP Tests
      run: |
        python test_mcp_client.py
        python test_mcp_direct.py
    - name: Upload Results
      uses: actions/upload-artifact@v3
      with:
        name: mcp-test-results
        path: mcp_*_test_results_*.json
```

## Contributing

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Include comprehensive docstrings
3. Use type hints for all function parameters and returns
4. Add specific exception handling
5. Update this README with new test descriptions

## License

This test suite is part of the Archon project. See the main project license for details.
