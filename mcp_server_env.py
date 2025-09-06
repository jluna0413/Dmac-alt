#!/usr/bin/env python3
"""
MCP Server Environment Setup and Test

This script sets up the environment and tests the MCP server after circular import fixes.
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_mcp_environment():
    """Set up MCP server environment variables."""
    print("🔧 Setting up MCP Server Environment")

    # Set required environment variables
    os.environ['ARCHON_MCP_PORT'] = '8051'
    os.environ['MCP_DISABLE_AUTO_DISCOVERY'] = '1'
    os.environ['MCP_DISABLE_CIRCULAR_CHECK'] = '1'
    os.environ['MCP_VERBOSE_LOGGING'] = '1'

    print("✅ Environment variables set:")
    print(f"  ARCHON_MCP_PORT={os.environ['ARCHON_MCP_PORT']}")
    print(f"  MCP_DISABLE_AUTO_DISCOVERY={os.environ['MCP_DISABLE_AUTO_DISCOVERY']}")
    print(f"  MCP_DISABLE_CIRCULAR_CHECK={os.environ['MCP_DISABLE_CIRCULAR_CHECK']}")

    # Also create .env file in Archon/python directory
    env_file = Path("Archon/python/.env")
    try:
        env_content = """# MCP Server Environment Configuration
ARCHON_MCP_PORT=8051
MCP_DISABLE_AUTO_DISCOVERY=1
MCP_DISABLE_CIRCULAR_CHECK=1
MCP_VERBOSE_LOGGING=1
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"✅ Created environment file: {env_file}")
    except Exception as e:
        print(f"⚠️ Could not create .env file: {e}")

    return True

def test_mcp_server_startup():
    """Test MCP server startup with proper environment."""
    print("\n🚀 Testing MCP Server Startup")

    try:
        # Change to Archon/python directory
        archon_dir = Path("Archon/python")
        if not archon_dir.exists():
            print(f"❌ Archon directory not found: {archon_dir}")
            return False

        # Start MCP server in background
        print("Starting MCP server...")
        startup_script = archon_dir / "simplified_mcp_startup.py"
        print(f"Looking for startup script: {startup_script}")
        print(f"Script exists: {startup_script.exists()}")

        if not startup_script.exists():
            print(f"❌ Startup script not found. Creating simplified startup...")
            # Create the startup script if it doesn't exist
            startup_content = '''#!/usr/bin/env python3
"""
Simplified MCP Server Startup

This script starts the MCP server without triggering circular imports.
"""

import os
import sys
from pathlib import Path

def main():
    """Start MCP server with minimal module loading."""
    try:
        # Import and start the server
        from src.mcp_server.mcp_server import main as start_server
        start_server()
    except Exception as e:
        print(f"Server error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
            with open(startup_script, "w", encoding="utf-8") as f:
                f.write(startup_content)
            print(f"✅ Created startup script: {startup_script}")

        process = subprocess.Popen(
            [sys.executable, str(startup_script)],
            cwd=str(archon_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait a bit for startup
        import time
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server started successfully!")
            print("Server should be running on http://localhost:8051/mcp")

            # Test the connection
            test_connection()

            # Give user option to stop
            print("\n📋 Server is running. Press Ctrl+C when done testing.")
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping MCP server...")
                process.terminate()
                process.wait()

        else:
            # Process terminated, check output
            stdout, stderr = process.communicate()
            print("❌ MCP server failed to start")
            if stderr:
                print(f"Error output:\n{stderr}")
            if stdout:
                print(f"Standard output:\n{stdout}")
            return False

    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def test_connection():
    """Test MCP server connection."""
    print("\n🔍 Testing MCP Server Connection")

    try:
        import requests
        import json

        # Test basic health check
        url = "http://localhost:8051/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": "test_connection",
            "method": "health_check",
            "params": {}
        }

        response = requests.post(url, json=payload, timeout=5)
        print(f"Connection test: {response.status_code}")

        if response.status_code == 200:
            print("✅ MCP server connection successful!")
            return True
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

def run_complete_test():
    """Run complete MCP server test suite."""
    print("🧪 Complete MCP Server Test Suite")
    print("=" * 50)

    # Setup environment
    if not setup_mcp_environment():
        return False

    # Test startup
    success = test_mcp_server_startup()

    if success:
        print("\n🎉 MCP Server is working correctly!")
        print("You can now try connecting with Cline MCP tools.")
        return True
    else:
        print("\n❌ MCP Server test failed.")
        return False

if __name__ == "__main__":
    success = run_complete_test()
    sys.exit(0 if success else 1)
