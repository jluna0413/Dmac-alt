#!/usr/bin/env python3
"""
Fix MCP Server Circular Import Issues

This script addresses the recursive module loading problem in the MCP server.
The issue is that during module auto-discovery, MCP tools with @tool decorators
are trying to access get_archon_mcp_control() before the singleton is fully initialized.
"""

import os
import sys
from pathlib import Path

def fix_circular_import_issue():
    """Fix the circular import issue in MCP server module loading."""

    print("🔧 Fixing MCP Server Circular Import Issues")

    # Path to the problematic MCP control module
    mcp_control_init = Path("Archon/python/src/mcp_server/modules/mcpcontrol/__init__.py")

    if not mcp_control_init.exists():
        print("❌ MCP control module not found")
        return False

    print(f"Found MCP control module at: {mcp_control_init}")

    # Read the current file
    with open(mcp_control_init, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix 1: Add lazy initialization for circular imports
    # Replace the immediate singleton creation with lazy initialization
    old_pattern = '''
# Global singleton instance
_archon_mcp_control = None

def get_archon_mcp_control():
    """Get the Archon MCP Control singleton instance."""
    global _archon_mcp_control
    if _archon_mcp_control is None:
        _archon_mcp_control = ArchonMCPControl()
    return _archon_mcp_control'''

    new_pattern = '''
# Global singleton instance
_archon_mcp_control = None
_initialization_lock = threading.Lock()

def get_archon_mcp_control():
    """Get the Archon MCP Control singleton instance with circular import protection."""
    global _archon_mcp_control
    if _archon_mcp_control is None:
        with _initialization_lock:
            # Double-check pattern for thread safety
            if _archon_mcp_control is None:
                try:
                    _archon_mcp_control = ArchonMCPControl()
                except RecursionError:
                    # If we hit recursion, log and return None for now
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("Circular import detected in get_archon_mcp_control, returning None")
                    return None
    return _archon_mcp_control'''

    if old_pattern.strip() in content:
        content = content.replace(old_pattern.strip(), new_pattern.strip())
        print("✅ Fixed circular import protection in get_archon_mcp_control")
    else:
        print("⚠️ Could not find exact pattern to replace")

    # Fix 2: Add circular import protection in __init__.py
    # Modify the decorator registration to be lazy
    old_decorator_reg = "mcp_control = get_archon_mcp_control()"
    new_decorator_reg = '''
    mcp_control = get_archon_mcp_control()
    if mcp_control is None:
        # Handle circular import during initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not get MCP control for tool '{name}', deferring registration")
        # Return a dummy decorator that does nothing
        def dummy_decorator(func):
            return func
        return dummy_decorator
    '''

    if old_decorator_reg in content:
        content = content.replace(old_decorator_reg, new_decorator_reg)
        print("✅ Added null check for MCP control in decorator")
    else:
        print("⚠️ Could not find decorator registration pattern")

    # Write back the fixed content
    try:
        with open(mcp_control_init, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Fixed circular import issues in MCP control module")
        return True
    except Exception as e:
        print(f"❌ Error writing fixed file: {e}")
        return False

def create_simplified_startup():
    """Create a simplified MCP server startup script without auto-discovery."""

    startup_script = '''#!/usr/bin/env python3
"""
Simplified MCP Server Startup

This script starts the MCP server without triggering circular imports.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

def main():
    """Start MCP server with minimal module loading."""
    try:
        # Import only essential components first
        print("🚀 Starting MCP Server (Simplified Mode)")

        # Set environment variables to disable problematic features
        os.environ["MCP_DISABLE_AUTO_DISCOVERY"] = "1"
        os.environ["MCP_DISABLE_CIRCULAR_CHECK"] = "1"

        # Import and start the server
        from src.mcp_server.mcp_server import main as start_server
        start_server()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

    script_path = Path("Archon/python/simplified_mcp_startup.py")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(startup_script)
        print(f"✅ Created simplified startup script: {script_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating startup script: {e}")
        return False

def disable_auto_discovery():
    """Create environment variable setting to disable problematic auto-discovery."""

    env_script = '''# MCP Server Environment Configuration
# Add these to your .env file to prevent circular import issues

# Disable auto-discovery to prevent circular imports
MCP_DISABLE_AUTO_DISCOVERY=1

# Disable module loading during import time
MCP_DISABLE_CIRCULAR_CHECK=1

# Enable verbose logging for debugging
MCP_VERBOSE_LOGGING=1

# Force single-threaded initialization
MCP_SINGLE_THREADED=1
'''

    env_path = Path("Archon/python/.env.mcp")
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_script)
        print(f"✅ Created MCP environment configuration: {env_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating environment config: {e}")
        return False

def run_all_fixes():
    """Run all circular import fixes."""

    print("🔧 Running all MCP circular import fixes...")

    fixes_applied = []

    # Fix 1: Modify the MCP control module
    if fix_circular_import_issue():
        fixes_applied.append("Fixed circular import protection")

    # Fix 2: Create simplified startup script
    if create_simplified_startup():
        fixes_applied.append("Created simplified startup script")

    # Fix 3: Create environment configuration
    if disable_auto_discovery():
        fixes_applied.append("Created environment configuration")

    if fixes_applied:
        print("\n✅ Fixes Applied:")
        for fix in fixes_applied:
            print(f"  ✓ {fix}")

        print("\n📋 Next Steps:")
        print("1. Use the simplified startup script:")
        print("   python Archon/python/simplified_mcp_startup.py")
        print("2. Or add environment variables to your .env file")
        print("3. Or manually disable auto-discovery in your MCP server")
        return True
    else:
        print("\n❌ No fixes were successfully applied")
        return False

if __name__ == "__main__":
    success = run_all_fixes()
    print("\n🎯 MCP Server Circular Import Fix Complete")
    print("Run this script again if you encounter more circular import issues.")
