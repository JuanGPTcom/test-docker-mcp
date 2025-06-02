"""MCP tools for Odoo operations."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import mcp.types as types
from pydantic import BaseModel, Field

from .odoo_client import OdooClient


class BaseTool(ABC):
    """Base class for all Odoo tools."""
    
    def __init__(self, client: Optional[OdooClient] = None):
        self.client = client
        
    @classmethod
    @abstractmethod
    def get_tool_definition(cls) -> types.Tool:
        """Get MCP tool definition."""
        pass
        
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the tool with given arguments."""
        pass
        
    def format_result(self, result: Any) -> str:
        """Format result as JSON string."""
        return json.dumps(result, indent=2, default=str)


class OdooAuthenticateTool(BaseTool):
    """Tool for authenticating with Odoo."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_authenticate",
            description="Authenticate with an Odoo instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Odoo server URL (e.g., https://mycompany.odoo.com)"
                    },
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username for authentication"
                    },
                    "password": {
                        "type": "string",
                        "description": "Password for authentication"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key for authentication (Odoo 14+, use instead of password)"
                    }
                },
                "required": ["url", "database"],
                "oneOf": [
                    {"required": ["username", "password"]},
                    {"required": ["username", "api_key"]}
                ]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        # This is handled in the server directly
        return self.format_result({"success": True})


class OdooSearchTool(BaseTool):
    """Tool for searching Odoo records."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_search",
            description="Search for records in an Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name (e.g., 'res.partner', 'sale.order')"
                    },
                    "domain": {
                        "type": "array",
                        "description": "Search domain (e.g., [['is_company', '=', True]])",
                        "items": {"type": "array"}
                    },
                    "fields": {
                        "type": "array",
                        "description": "Fields to return (optional)",
                        "items": {"type": "string"}
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip",
                        "default": 0
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order (e.g., 'name asc')"
                    }
                },
                "required": ["model", "domain"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        result = await self.client.search_read(
            model=arguments["model"],
            domain=arguments["domain"],
            fields=arguments.get("fields"),
            limit=arguments.get("limit"),
            offset=arguments.get("offset", 0),
            order=arguments.get("order")
        )
        return self.format_result(result)


class OdooReadTool(BaseTool):
    """Tool for reading Odoo records by IDs."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_read",
            description="Read specific records by their IDs",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs",
                        "items": {"type": "integer"}
                    },
                    "fields": {
                        "type": "array",
                        "description": "Fields to return (optional)",
                        "items": {"type": "string"}
                    }
                },
                "required": ["model", "ids"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        result = await self.client.read(
            model=arguments["model"],
            ids=arguments["ids"],
            fields=arguments.get("fields")
        )
        return self.format_result(result)


class OdooCreateTool(BaseTool):
    """Tool for creating Odoo records."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_create",
            description="Create a new record in an Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values for the new record"
                    }
                },
                "required": ["model", "values"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        record_id = await self.client.create(
            model=arguments["model"],
            values=arguments["values"]
        )
        return self.format_result({
            "success": True,
            "id": record_id,
            "message": f"Created record with ID {record_id}"
        })


class OdooUpdateTool(BaseTool):
    """Tool for updating Odoo records."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_update",
            description="Update existing records in an Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs to update",
                        "items": {"type": "integer"}
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values to update"
                    }
                },
                "required": ["model", "ids", "values"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        success = await self.client.write(
            model=arguments["model"],
            ids=arguments["ids"],
            values=arguments["values"]
        )
        return self.format_result({
            "success": success,
            "ids": arguments["ids"],
            "message": f"Updated {len(arguments['ids'])} record(s)"
        })


class OdooDeleteTool(BaseTool):
    """Tool for deleting Odoo records."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_delete",
            description="Delete records from an Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs to delete",
                        "items": {"type": "integer"}
                    }
                },
                "required": ["model", "ids"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        success = await self.client.unlink(
            model=arguments["model"],
            ids=arguments["ids"]
        )
        return self.format_result({
            "success": success,
            "ids": arguments["ids"],
            "message": f"Deleted {len(arguments['ids'])} record(s)"
        })


class OdooExecuteTool(BaseTool):
    """Tool for executing arbitrary Odoo methods."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_execute",
            description="Execute arbitrary methods on Odoo models (advanced use)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "method": {
                        "type": "string",
                        "description": "Method name to execute"
                    },
                    "args": {
                        "type": "array",
                        "description": "Positional arguments for the method",
                        "items": {}
                    },
                    "kwargs": {
                        "type": "object",
                        "description": "Keyword arguments for the method"
                    }
                },
                "required": ["model", "method"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        args = arguments.get("args", [])
        kwargs = arguments.get("kwargs", {})
        
        result = await self.client.execute(
            model=arguments["model"],
            method=arguments["method"],
            *args,
            **kwargs
        )
        return self.format_result(result)


class OdooListModelsTool(BaseTool):
    """Tool for listing available Odoo models."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_list_models",
            description="List all available models in the Odoo instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "Optional filter for model names"
                    }
                }
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        # Search for all models
        model_ids = await self.client.search(
            model="ir.model",
            domain=[]
        )
        
        # Read model information
        models = await self.client.read(
            model="ir.model",
            ids=model_ids,
            fields=["model", "name", "info"]
        )
        
        # Apply filter if provided
        filter_str = arguments.get("filter", "").lower()
        if filter_str:
            models = [
                m for m in models
                if filter_str in m["model"].lower() or 
                   filter_str in m["name"].lower()
            ]
            
        # Sort by model name
        models.sort(key=lambda x: x["model"])
        
        return self.format_result(models)


class OdooGetFieldsTool(BaseTool):
    """Tool for getting field definitions of a model."""
    
    @classmethod
    def get_tool_definition(cls) -> types.Tool:
        return types.Tool(
            name="odoo_get_fields",
            description="Get field definitions for a specific Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "attributes": {
                        "type": "array",
                        "description": "Specific field attributes to return (optional)",
                        "items": {"type": "string"}
                    }
                },
                "required": ["model"]
            }
        )
        
    async def execute(self, arguments: Dict[str, Any]) -> str:
        fields = await self.client.execute(
            model=arguments["model"],
            method="fields_get",
            attributes=arguments.get("attributes")
        )
        return self.format_result(fields)