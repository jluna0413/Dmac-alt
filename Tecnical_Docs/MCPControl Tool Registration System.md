# MCPControl Tool Registration System

## Overview

The MCPControl Tool Registration System provides an efficient and flexible way to register tools for use with Archon and VS Code assistants. It addresses issues with redundant registrations and offers a cleaner, more maintainable approach to tool definition.

## Key Features

- **Decorator-based Tool Definition**: Define tools using simple decorators
- **Module-based Registration**: Register all tools in a module with a single call
- **Duplicate Registration Prevention**: Automatically tracks and prevents redundant registrations
- **Module Tracking**: Associate tools with their source modules for better organization

## Registration Methods

### 1. Decorator-based Registration

The decorator approach allows for clean, declarative tool definitions:

```python
from mcp_server.modules.mcpcontrol.tools import tool

@tool(
    name="my_tool",
    description="My custom tool",
    parameters={
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input parameter"}
        }
    },
    tags=["category:example", "assistant:roocode"]
)
def my_tool_handler(params):
    """Handle my tool invocation."""
    # Implementation
    return {"result": "Success"}
```

### 2. Module-based Registration

Register an entire module's tools at once:

```python
# Get the MCPControl singleton
from mcp_server.modules.mcpcontrol import get_archon_mcp_control

# Register all tools from a module
mcp = get_archon_mcp_control()
mcp.tool_registry.register_module("my_module")
```

### 3. Direct Registration (Legacy)

For backward compatibility, direct registration is still supported:

```python
registry.register_tool(
    name="my_tool",
    description="My custom tool",
    parameters={...},
    handler=my_tool_handler,
    tags=["custom", "example"],
    module="my_module"  # New: specify module source
)
```

## How It Works

1. **Tool Decorator**:
   - Attaches metadata to functions
   - Makes code more readable and maintainable

2. **Registry Tracking**:
   - Keeps track of registered tools and modules
   - Prevents duplicate registrations
   - Associates tools with their source modules

3. **Module Registration System**:
   - Imports modules and registers all tools defined within
   - Prevents circular imports and duplicate registrations
   - Allows for modular organization of tools

## Best Practices

1. **Organize Tools by Module**:
   - Group related tools in the same module
   - Use consistent naming conventions

2. **Use Descriptive Tags**:
   - Tag tools with assistant types they support (`assistant:roocode`)
   - Tag tools with categories (`category:code`, `category:devops`)

3. **Avoid Direct Registration**:
   - Prefer decorator-based or module-based registration
   - Use direct registration only for dynamic tools

4. **Module Structure**:
   - Define tools in a `tools.py` file in your module
   - Implement a `register_tools()` function in your module's tools file

## Integration with Assistant Types

Tools can be filtered by assistant type using tags:

- **RooCode**: Code-related tools (`code`, `refactor`, `debug`)
- **CLine**: Terminal and DevOps tools (`cli`, `devops`, `terminal`)
- **Continue**: All tools

## Future Improvements

- Auto-discovery of modules in the Archon project
- Runtime tool registration based on user configuration
- Tool versioning and dependency management
- Advanced filtering based on context and user permissions
