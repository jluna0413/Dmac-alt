# Guide to Using the Improved Tool Registration System

This guide explains how to use the improved tool registration system in the MCPControl module. It provides step-by-step instructions for creating new tools and modules using the new registration pattern.

## Benefits of the Improved Registration System

- **Prevents Duplicate Registrations**: Tools are registered only once
- **Simplified Tool Definition**: Use decorators to define tools
- **Automatic Registration**: Tools are registered automatically on import
- **Module Tracking**: Prevents recursive registrations

## Creating a New Tool

### 1. Create a tools.py file in your module

First, create a `tools.py` file in your module directory. This file will contain all your tool definitions.

```python
"""
Tools for your module.

This file contains all the tool definitions for your module.
"""

import logging
from typing import Dict, Any

from mcp_server.modules.mcpcontrol.tools import tool

logger = logging.getLogger(__name__)
```

### 2. Define your tools using the @tool decorator

Use the `@tool` decorator to define your tools. The decorator takes these parameters:

- `name`: The name of the tool, used to call it
- `description`: A brief description of what the tool does
- `parameters`: The JSON Schema for the tool's parameters
- `tags`: Optional list of tags for categorization

```python
@tool(
    name="my_module_hello",
    description="Get a greeting from my module",
    parameters={},
    tags=["greetings"]
)
def hello_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return a greeting."""
    return {"message": "Hello from my module!"}
```

### 3. Add a register_tools function

Although not strictly necessary with the decorator approach, it's good practice to include a `register_tools` function for explicit registration.

```python
def register_tools():
    """Register all tools in this module."""
    # No need to manually register tools, as they are decorated
    logger.info("My module tools registered")
```

## Creating a New Module

### 1. Create an __init__.py file

Create an `__init__.py` file in your module directory. This file will define your module and its registration function.

```python
"""
My module description.
"""

import logging
from . import tools

logger = logging.getLogger(__name__)


def register_module():
    """Register this module with the system."""
    logger.info("Registering My module")
    
    # In more complex modules, you might do additional setup here
    tools.register_tools()
```

### 2. Integrate with MCPControl

To use your module with MCPControl, simply import it. The import will trigger the registration process.

```python
from mcp_server.modules.mcpcontrol import MCPControl
import my_module  # This will register the module and its tools

mcpcontrol = MCPControl()
```

## Advanced Usage

### Handling Dependencies

If your module depends on other modules, import them in your `register_module` function:

```python
def register_module():
    """Register this module with the system."""
    # Import dependencies
    import other_module
    
    # Register tools
    tools.register_tools()
```

### Conditional Registration

If you need to conditionally register tools, you can do so in your `register_tools` function:

```python
def register_tools():
    """Register tools based on conditions."""
    if some_condition:
        # Register specific tools
        pass
    else:
        # Register other tools
        pass
```

### Tool Parameters

Define your tool parameters using JSON Schema format:

```python
@tool(
    name="my_tool",
    description="My tool description",
    parameters={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "First parameter"
            },
            "param2": {
                "type": "integer",
                "description": "Second parameter"
            }
        },
        "required": ["param1"]
    },
    tags=["category1"]
)
def my_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    # Handle the tool
    pass
```

## Best Practices

1. **Organize Tools by Function**: Group related tools in the same module
2. **Use Descriptive Names**: Use clear, descriptive names for your tools
3. **Document Parameters**: Clearly document each parameter
4. **Add Tags**: Use tags to categorize your tools
5. **Keep Handlers Simple**: Each tool handler should do one thing well
6. **Validate Input**: Validate input parameters in your handler
7. **Handle Errors**: Properly handle errors in your tool handlers
8. **Test Your Tools**: Write unit tests for your tools

## Example

See the example module in `src/mcp_server/modules/example/` for a complete implementation of these best practices.

## Troubleshooting

### Tool Not Registered

If your tool is not being registered:

1. Make sure you're using the `@tool` decorator
2. Check that your module is being imported
3. Verify that the tool name is unique

### Multiple Registrations

If you're seeing multiple registrations of the same tool:

1. Check for circular imports
2. Ensure you're using the latest MCPControl

### Import Errors

If you're seeing import errors:

1. Check your Python path
2. Verify that all dependencies are installed
3. Check for circular dependencies

## Conclusion

The improved registration system makes it easier to define and register tools with MCPControl. By using the decorator pattern and automatic registration, you can focus on building great tools without worrying about registration boilerplate.
