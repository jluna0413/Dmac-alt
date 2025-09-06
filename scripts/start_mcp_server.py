#!/usr/bin/env python3
"""
Script to start the Archon MCP server properly
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the MCP server on port 8051"""
    print("🚀 Starting Archon MCP Server...")

    # Set the environment variable for MCP port
    os.environ["ARCHON_MCP_PORT"] = "8051"

    # Change to the Archon python directory
    archon_dir = Path(__file__).parent.parent / "Archon" / "python"
    os.chdir(archon_dir)

    # Add the current directory to Python path
    sys.path.insert(0, str(archon_dir))

    print(f"📁 Working directory: {archon_dir}")
    print(f"🔧 MCP Port: {os.environ.get('ARCHON_MCP_PORT')}")

    # Run the MCP server
    try:
        cmd = [sys.executable, "src/mcp_server/mcp_server.py"]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("👋 MCP server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
