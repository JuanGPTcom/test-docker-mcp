#!/usr/bin/env python3
"""MCP server for Odoo XML-RPC API."""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from pydantic import BaseModel

from .odoo_client import OdooClient, OdooConfig
from .tools import (
    OdooAuthenticateTool,
    OdooSearchTool,
    OdooReadTool,
    OdooCreateTool,
    OdooUpdateTool,
    OdooDeleteTool,
    OdooExecuteTool,
    OdooListModelsTool,
    OdooGetFieldsTool
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OdooMCPServer:
    """Main MCP server for Odoo integration."""
    
    def __init__(self):
        self.server = Server("odoo-mcp-server")
        self.odoo_client: Optional[OdooClient] = None
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List all available Odoo tools."""
            return [
                OdooAuthenticateTool.get_tool_definition(),
                OdooSearchTool.get_tool_definition(),
                OdooReadTool.get_tool_definition(),
                OdooCreateTool.get_tool_definition(),
                OdooUpdateTool.get_tool_definition(),
                OdooDeleteTool.get_tool_definition(),
                OdooExecuteTool.get_tool_definition(),
                OdooListModelsTool.get_tool_definition(),
                OdooGetFieldsTool.get_tool_definition()
            ]
            
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution."""
            
            try:
                # Handle authentication separately
                if name == "odoo_authenticate":
                    tool = OdooAuthenticateTool()
                    result = await tool.execute(arguments)
                    
                    # Create and store the client
                    config = OdooConfig(
                        url=arguments["url"],
                        database=arguments["database"],
                        username=arguments.get("username"),
                        password=arguments.get("password"),
                        api_key=arguments.get("api_key")
                    )
                    self.odoo_client = OdooClient(config)
                    await self.odoo_client.connect()
                    
                    return [types.TextContent(type="text", text=result)]
                
                # Check if authenticated
                if not self.odoo_client or not self.odoo_client.is_connected:
                    return [types.TextContent(
                        type="text",
                        text="Error: Not authenticated. Please use odoo_authenticate first."
                    )]
                
                # Execute the appropriate tool
                tool_map = {
                    "odoo_search": OdooSearchTool,
                    "odoo_read": OdooReadTool,
                    "odoo_create": OdooCreateTool,
                    "odoo_update": OdooUpdateTool,
                    "odoo_delete": OdooDeleteTool,
                    "odoo_execute": OdooExecuteTool,
                    "odoo_list_models": OdooListModelsTool,
                    "odoo_get_fields": OdooGetFieldsTool
                }
                
                tool_class = tool_map.get(name)
                if not tool_class:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Unknown tool {name}"
                    )]
                
                tool = tool_class(self.odoo_client)
                result = await tool.execute(arguments)
                
                return [types.TextContent(type="text", text=result)]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                initialize_params=types.InitializeParams(
                    server_name="odoo-mcp-server",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {
                            "call": {
                                "enabled": True
                            }
                        }
                    }
                )
            )


def main():
    """Main entry point."""
    # Load configuration from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    server = OdooMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()