# MCPControl Integration Guide

## Overview

Archon now includes an integrated MCPControl module for managing MCP connections, tool registrations, and session persistence. This module enables seamless integration between Archon and VS Code assistants, allowing for workflow orchestration and task distribution.

## MCPControl Components

The MCPControl implementation consists of three main components:

1. **ConnectionManager**: Manages connections to MCP servers (both Archon and VS Code)
2. **ToolRegistry**: Handles tool registration, discovery, and execution
3. **SessionController**: Provides session persistence and context sharing

## Integration with VS Code Assistants

MCPControl integrates with the following VS Code assistants:

- **RooCode**: Specializes in code implementation tasks
- **CLine**: Handles command-line and terminal operations
- **Continue**: Manages long-running tasks and workflows

Each assistant has access to a filtered set of tools based on its capabilities and responsibilities.

## Getting Started

To use MCPControl in your Archon module:

```python
from mcp_server.modules.mcpcontrol import get_archon_mcp_control

# Get the MCPControl singleton
mcp = get_archon_mcp_control()

# Create a session
session_id = mcp.create_session("My Session", "RooCode")

# Get tools for a specific assistant
tools = mcp.get_tools_for_assistant("RooCode")
```

## Configuration

MCPControl can be configured using environment variables or a JSON configuration file:

- **ARCHON_MCPCONTROL_CONFIG**: Path to configuration file
- **ARCHON_MCP_URL**: URL for Archon MCP server
- **ARCHON_AUTH_TOKEN**: Authentication token for Archon MCP server
- **VSCODE_MCP_URL**: URL for VS Code MCP server
- **VSCODE_AUTH_TOKEN**: Authentication token for VS Code MCP server
- **ARCHON_SESSION_STORAGE**: Path for session storage

## Installation and Setup

To set up MCPControl integration:

1. Run the setup script:
   ```
   python -m mcp_server.modules.mcpcontrol setup
   ```

2. Install dependencies:
   ```
   pip install -e ".[mcp]"
   ```

3. Test the integration:
   ```
   python -m mcp_server.modules.mcpcontrol test
   ```

## Custom Tool Registration

To register custom tools:

```python
from mcp_server.modules.mcpcontrol import get_archon_mcp_control

# Get the MCPControl singleton
mcp = get_archon_mcp_control()
registry = mcp.tool_registry

# Define a tool handler
def my_tool_handler(params):
    # Implement tool logic
    return {"result": "Success"}

# Register a tool
registry.register_tool(
    name="my_tool",
    description="My custom tool",
    parameters={
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "Input parameter"
            }
        }
    },
    handler=my_tool_handler,
    tags=["custom", "example"]
)
```

## Workflow Orchestration

MCPControl enables workflow orchestration between Archon and VS Code assistants through:

1. **Session Context Sharing**: Persistent context shared between assistants
2. **Tool Discovery and Filtering**: Assistant-specific tool access
3. **Connection Management**: Communication with different MCP servers

This integration allows for complex workflows where different assistants handle specific aspects of a larger task, with Archon acting as the central coordination point.

## Future Enhancements

Planned enhancements for the MCPControl integration include:

1. **Tool Invocation Logging**: Comprehensive logging of tool usage
2. **Access Control**: Fine-grained control over tool access
3. **Context Serialization**: Improved serialization for complex context data
4. **Remote Tool Execution**: Execute tools on remote MCP servers
