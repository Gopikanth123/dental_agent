# mcp_server/run.py
import sys
import os

# Ensure the project root is in python path so we can import database/utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.server import mcp
# Import tools to register them with the server
import mcp_server.tools 

if __name__ == "__main__":
    # This runs the MCP server over stdio (standard input/output)
    mcp.run()