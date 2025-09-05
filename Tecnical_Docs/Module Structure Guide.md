# Archon MCP Server Module Structure Guide

## Overview

The Archon MCP Server uses a modular architecture with automatic discovery and registration of modules. This document outlines the structure and provides best practices for module development.

## Directory Structure

```
mcp_server/
├── modules/                    # Standard modules directory
│   ├── example/               # Legacy example module
│   ├── example_module/        # New example module with @tool decorators
│   ├── mcpcontrol/           # Core MCP control functionality
│   ├── rag_module.py         # RAG and web crawling tools
│   ├── terminal/             # Terminal-related tools
│   └── auto_discovery.py     # Auto-discovery mechanism
├── example_modules/           # Example modules for demonstration
│   ├── direct_registration/   # Direct registration example
│   └── traditional_tools/     # Traditional tools.py example
└── mcp_server.py             # Main server entry point
```

## Module Types

### 1. Standard Modules (`modules/`)
These are production modules that ship with the server:
- **example/**: Legacy example showing basic registration
- **example_module/**: Modern example with @tool decorators
- **mcpcontrol/**: Core MCP functionality
- **rag_module.py**: RAG and web crawling capabilities
- **terminal/**: Terminal interaction tools

### 2. Example Modules (`example_modules/`)
These are educational examples showing different registration patterns:
- **direct_registration/**: Shows direct registration in `__init__.py`
- **traditional_tools/**: Shows traditional `tools.py` approach

## Registration Patterns

### Pattern 1: Direct Registration (Recommended)
File: `module_name/__init__.py`
```python
from mcp_server.modules.mcpcontrol import get_tool_registry

def register_module() -> bool:
    registry = get_tool_registry()
    registry.register_tool(...)
    return True
```

### Pattern 2: Tools File Registration
Files: `module_name/__init__.py` + `module_name/tools.py`
```python
# tools.py
def register_tools() -> None:
    registry = get_tool_registry()
    registry.register_tool(...)
```

### Pattern 3: Decorator-Based Registration
File: `module_name/tools.py`
```python
from mcp_server.modules.mcpcontrol.tools import tool

@tool(name="tool_name", description="...")
def tool_function(params):
    return {"result": "..."}
```

## Best Practices

1. **Use Descriptive Names**: Module names should be clear and descriptive
2. **Include Documentation**: Add proper docstrings to all modules and functions
3. **Error Handling**: Implement proper error handling in registration functions
4. **Return Values**: `register_module()` should return `bool`, `register_tools()` returns `None`
5. **Logging**: Use the module logger for registration status

## Testing Modules

Use the provided test scripts:
- `tests/test_module_discovery.py` - Tests module importability and registration
- `tests/test_example_module.py` - Full integration test (requires MCP server)

## Creating New Modules

Use the module creation utility:
```bash
python src/mcp_server/create_module.py my_module --description "My module description"
```

This creates a properly structured module with all necessary files and templates.

## Auto-Discovery Process

1. Server scans `modules/` and `example_modules/` directories
2. Identifies directories with `__init__.py` files
3. Attempts registration in order:
   - Import `__init__.py` and call `register_module()`
   - Fall back to importing `tools.py` and call `register_tools()`
4. Logs registration results

## Troubleshooting

### Module Not Discovered
- Ensure module has `__init__.py` file
- Check module name doesn't contain special characters
- Verify module is in correct directory

### Registration Fails
- Check import paths are correct
- Verify all dependencies are available
- Review server logs for specific errors

### Tools Not Working
- Ensure tools are properly registered
- Check tool parameter schemas
- Verify handler functions work correctly

## Migration Guide

### From Legacy to Modern
1. Move from simple registration to @tool decorators
2. Update error handling to return proper status codes
3. Add comprehensive parameter validation
4. Include proper logging and documentation

### Adding New Functionality
1. Create new module using the creation utility
2. Implement tools using recommended patterns
3. Test with discovery test script
4. Document new tools and functionality

For more detailed information on the auto-discovery mechanism, see:
`/Technical_Docs/Module Auto-Discovery Mechanism.md`
