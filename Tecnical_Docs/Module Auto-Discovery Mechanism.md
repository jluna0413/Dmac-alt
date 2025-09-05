# Module Auto-Discovery Mechanism

## Overview

The Archon MCP Server implements a sophisticated module auto-discovery mechanism that allows for seamless integration of new functionality without manual registration. This document explains how the system works, how to create modules that can be automatically discovered, and the different approaches for registering tools.

## How Auto-Discovery Works

When the MCP Server starts up, it automatically scans two primary directories for modules:

1. `mcp_server/modules/` - For standard modules that ship with the server
2. `mcp_server/example_modules/` - For example and user-created modules

The auto-discovery process performs the following steps:

1. Identifies all directories with an `__init__.py` file
2. For each identified module, it attempts to register it using one of two approaches:
   - Direct registration via `register_module()` in the module's `__init__.py`
   - Traditional registration via `register_tools()` in the module's `tools.py`

## Creating Auto-Discoverable Modules

There are two main approaches to create modules that can be automatically discovered:

### Approach 1: Direct Registration (Recommended)

In this approach, the module registration logic is placed directly in the `__init__.py` file:

```python
"""
Your Module Description

This module provides functionality for...
"""
import logging
from typing import Dict, Any

# Get the global tool registry
from mcp_server.modules.mcpcontrol import get_tool_registry

logger = logging.getLogger(__name__)

def your_tool_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Your tool implementation."""
    # Implement your tool logic here
    return {"result": "Tool response"}

def register_module() -> bool:
    """
    Register all tools provided by this module with the tool registry.
    
    This function is automatically called by the auto-discovery mechanism
    when the module is loaded.
    
    Returns:
        bool: True if registration was successful, False otherwise
    """
    try:
        # Get the tool registry
        registry = get_tool_registry()
        
        # Register your tool(s)
        registry.register_tool(
            name="your_tool_name",
            description="Your tool description",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of parameter"
                    }
                }
            },
            handler=your_tool_handler,
            tags=["your-tag"],
            version="1.0.0",
            module="your_module_name"
        )
        
        logger.info("Successfully registered module tools")
        return True
    except Exception as e:
        logger.error(f"Error registering module tools: {e}")
        return False
```

### Approach 2: Traditional Tools File

This approach separates tool implementations into a separate `tools.py` file:

**`__init__.py`**:
```python
"""Your Module Description."""
# The __init__.py file can be minimal when using the tools.py approach
```

**`tools.py`**:
```python
"""
Your Module Tools

This file contains tool implementations for...
"""
import logging
from typing import Dict, Any

# Get the global tool registry
from mcp_server.modules.mcpcontrol import get_tool_registry

logger = logging.getLogger(__name__)

def your_tool_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Your tool implementation."""
    # Implement your tool logic here
    return {"result": "Tool response"}

def register_tools() -> None:
    """
    Register all tools provided by this module with the tool registry.
    
    This function is automatically called by the auto-discovery mechanism
    when the module is loaded.
    """
    try:
        # Get the tool registry
        registry = get_tool_registry()
        
        # Register your tool(s)
        registry.register_tool(
            name="your_tool_name",
            description="Your tool description",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of parameter"
                    }
                }
            },
            handler=your_tool_handler,
            tags=["your-tag"],
            version="1.0.0",
            module="your_module_name"
        )
        
        logger.info("Successfully registered module tools")
    except Exception as e:
        logger.error(f"Error registering module tools: {e}")
```

## Module Structure

A typical module should have the following structure:

```
your_module/
│
├── __init__.py            # Module initialization and optional direct registration
├── tools.py               # Tool implementations and traditional registration (optional)
├── your_submodule.py      # Additional module functionality
└── ...                    # Other module files
```

## Registration Process

The registration process follows this sequence:

1. The server identifies directories with `__init__.py` files in the modules directories
2. For each module, it attempts to import the module's `__init__.py` and call `register_module()` if it exists
3. If `register_module()` doesn't exist or fails, it falls back to importing `tools.py` and calling `register_tools()`
4. Each successful registration adds the module to the registry and enables its tools

## Best Practices

1. **Choose One Approach**: Use either direct registration or the traditional approach for a module, not both
2. **Return Status**: Make sure `register_module()` returns `True` for successful registration or `False` otherwise
3. **Error Handling**: Add proper error handling in your registration functions to catch and log any issues
4. **Logging**: Use the logger to provide clear information about the registration process
5. **Module Name**: Keep module names clear, descriptive, and free of spaces or special characters
6. **Documentation**: Include docstrings explaining your module's purpose and each tool's functionality

## Example Modules

The server includes example modules that demonstrate both approaches:

1. **Direct Registration Example**:  
   Located at `mcp_server/example_modules/direct_registration/`

2. **Traditional Tools Example**:  
   Located at `mcp_server/example_modules/traditional_tools/`

These examples can be used as templates for creating new modules.

## Troubleshooting

If your module is not being discovered or registered correctly:

1. **Check Module Structure**: Ensure your module has the correct file structure
2. **Check Function Names**: Verify that the registration functions are named correctly
3. **Check Return Values**: Make sure `register_module()` returns a boolean value
4. **Review Logs**: Examine the server logs for any errors or warnings during module registration
5. **Import Errors**: Verify all imports in your module are correct and the required dependencies are available

## Conclusion

The module auto-discovery mechanism makes extending the MCP Server with new functionality straightforward. By following the patterns described in this document, developers can create modules that are automatically discovered and registered with the server, eliminating the need for manual registration and reducing the potential for errors.
