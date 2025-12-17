# mcp_server/run.py
import sys
import os
import logging # Import logging

# Ensure the project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.server import mcp
import mcp_server.tools 
from logger_setup import setup_logging # Import the shared setup

if __name__ == "__main__":
    # Initialize logging for this subprocess
    setup_logging()
    
    # Create a local logger for startup message
    logger = logging.getLogger("MCP-Process")
    logger.info("MCP Server Subprocess Started")

    mcp.run()