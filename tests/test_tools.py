"""Tests for Odoo MCP tools."""

import pytest
import json
from unittest.mock import Mock, AsyncMock

from odoo_mcp_server.tools import (
    OdooSearchTool,
    OdooReadTool,
    OdooCreateTool,
    OdooUpdateTool,
    OdooDeleteTool
)


@pytest.fixture
def mock_client():
    """Create mock Odoo client."""
    client = Mock()
    client.search_read = AsyncMock()
    client.read = AsyncMock()
    client.create = AsyncMock()
    client.write = AsyncMock()
    client.unlink = AsyncMock()
    return client


class TestOdooTools:
    """Test MCP tools."""
    
    @pytest.mark.asyncio
    async def test_search_tool(self, mock_client):
        """Test search tool execution."""
        # Setup
        tool = OdooSearchTool(mock_client)
        mock_client.search_read.return_value = [
            {"id": 1, "name": "Test Partner"}
        ]
        
        # Execute
        result = await tool.execute({
            "model": "res.partner",
            "domain": [["is_company", "=", True]],
            "fields": ["name"],
            "limit": 10
        })
        
        # Verify
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "Test Partner"
        mock_client.search_read.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_tool(self, mock_client):
        """Test create tool execution."""
        # Setup
        tool = OdooCreateTool(mock_client)
        mock_client.create.return_value = 123
        
        # Execute
        result = await tool.execute({
            "model": "res.partner",
            "values": {"name": "New Partner"}
        })
        
        # Verify
        data = json.loads(result)
        assert data["success"] is True
        assert data["id"] == 123
        mock_client.create.assert_called_once_with(
            model="res.partner",
            values={"name": "New Partner"}
        )
        
    @pytest.mark.asyncio
    async def test_update_tool(self, mock_client):
        """Test update tool execution."""
        # Setup
        tool = OdooUpdateTool(mock_client)
        mock_client.write.return_value = True
        
        # Execute
        result = await tool.execute({
            "model": "res.partner",
            "ids": [1, 2],
            "values": {"phone": "+123456789"}
        })
        
        # Verify
        data = json.loads(result)
        assert data["success"] is True
        assert data["ids"] == [1, 2]
        mock_client.write.assert_called_once()