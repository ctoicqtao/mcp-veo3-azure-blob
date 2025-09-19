#!/usr/bin/env python3
"""
MCP Server wrapper with enhanced error handling and logging
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging for MCP deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mcp-veo3-server")

def main():
    """Main entry point with error handling"""
    try:
        logger.info("Starting MCP Veo3 Azure Blob server...")
        
        # Check required environment variables
        required_env_vars = ['GEMINI_API_KEY']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            sys.exit(1)
        
        # Check Azure configuration (optional but recommended)
        azure_connection = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not azure_connection:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set. Azure upload will be disabled.")
        else:
            logger.info("Azure Blob Storage configured successfully")
        
        # Import and run the main server
        from mcp_veo3_azure_blob import main as server_main
        logger.info("MCP server starting...")
        server_main()
        
    except ImportError as e:
        logger.error(f"Failed to import server module: {e}")
        logger.error("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
