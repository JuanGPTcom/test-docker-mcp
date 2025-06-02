# Odoo MCP Server

A production-ready MCP (Model Context Protocol) server for Odoo's XML-RPC API. This server allows AI assistants to interact with Odoo instances through a standardized interface.

## Features

- ? Complete XML-RPC integration (both `/xmlrpc/2/common` and `/xmlrpc/2/object` endpoints)
- ? Robust authentication with session management
- ? Connection pooling and automatic retry logic
- ? Comprehensive error handling
- ? All essential Odoo operations exposed as MCP tools
- ? Support for both password and API key authentication (Odoo 14+)

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/JuanGPTcom/test-docker-mcp.git
cd test-docker-mcp

# Install dependencies
pip install -e .
```

### 2. Configuration

Create a `.env` file in the project root:

```env
ODOO_URL=https://mycompany.odoo.com
ODOO_DATABASE=mycompany
ODOO_USERNAME=admin@mycompany.com
ODOO_PASSWORD=your-password
# Or for Odoo 14+, use API key instead:
# ODOO_API_KEY=your-api-key

# Optional settings
ODOO_TIMEOUT=30
ODOO_MAX_RETRIES=3
ODOO_RETRY_DELAY=1.0
```

### 3. Running the Server

```bash
# Using the installed command
odoo-mcp-server

# Or directly with Python
python -m odoo_mcp_server.server
```

### 4. Connect with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://mycompany.odoo.com",
        "ODOO_DATABASE": "mycompany",
        "ODOO_USERNAME": "admin@mycompany.com",
        "ODOO_PASSWORD": "your-password"
      }
    }
  }
}
```

## Available Tools

### 1. `odoo_authenticate`
Authenticate with an Odoo instance.

**Example:**
```json
{
  "tool": "odoo_authenticate",
  "arguments": {
    "url": "https://mycompany.odoo.com",
    "database": "mycompany",
    "username": "admin@mycompany.com",
    "password": "your-password"
  }
}
```

### 2. `odoo_search`
Search for records with domain filters.

**Example:**
```json
{
  "tool": "odoo_search",
  "arguments": {
    "model": "res.partner",
    "domain": [["is_company", "=", true]],
    "fields": ["name", "email", "phone"],
    "limit": 10
  }
}
```

### 3. `odoo_read`
Read specific records by IDs.

**Example:**
```json
{
  "tool": "odoo_read",
  "arguments": {
    "model": "res.partner",
    "ids": [1, 2, 3],
    "fields": ["name", "email"]
  }
}
```

### 4. `odoo_create`
Create new records.

**Example:**
```json
{
  "tool": "odoo_create",
  "arguments": {
    "model": "res.partner",
    "values": {
      "name": "New Customer",
      "email": "customer@example.com",
      "is_company": false
    }
  }
}
```

### 5. `odoo_update`
Update existing records.

**Example:**
```json
{
  "tool": "odoo_update",
  "arguments": {
    "model": "res.partner",
    "ids": [1],
    "values": {
      "phone": "+1234567890"
    }
  }
}
```

### 6. `odoo_delete`
Delete records.

**Example:**
```json
{
  "tool": "odoo_delete",
  "arguments": {
    "model": "res.partner",
    "ids": [123]
  }
}
```

### 7. `odoo_execute`
Execute arbitrary methods (advanced use).

**Example:**
```json
{
  "tool": "odoo_execute",
  "arguments": {
    "model": "sale.order",
    "method": "action_confirm",
    "args": [[123]]
  }
}
```

### 8. `odoo_list_models`
List available models.

**Example:**
```json
{
  "tool": "odoo_list_models",
  "arguments": {
    "filter": "sale"
  }
}
```

### 9. `odoo_get_fields`
Get field definitions for a model.

**Example:**
```json
{
  "tool": "odoo_get_fields",
  "arguments": {
    "model": "res.partner"
  }
}
```

## Common Use Cases

### Reading Contacts
```python
# Search for all companies
{
  "tool": "odoo_search",
  "arguments": {
    "model": "res.partner",
    "domain": [["is_company", "=", true]],
    "fields": ["name", "email", "phone", "website"],
    "limit": 50
  }
}
```

### Creating a Sales Order
```python
# First create the order
{
  "tool": "odoo_create",
  "arguments": {
    "model": "sale.order",
    "values": {
      "partner_id": 1,
      "date_order": "2024-01-01",
      "order_line": [
        [0, 0, {
          "product_id": 1,
          "product_uom_qty": 10,
          "price_unit": 100
        }]
      ]
    }
  }
}

# Then confirm it
{
  "tool": "odoo_execute",
  "arguments": {
    "model": "sale.order",
    "method": "action_confirm",
    "args": [[order_id]]
  }
}
```

### Updating Product Prices
```python
# Search for products
{
  "tool": "odoo_search",
  "arguments": {
    "model": "product.product",
    "domain": [["active", "=", true]],
    "fields": ["name", "list_price"],
    "limit": 100
  }
}

# Update prices
{
  "tool": "odoo_update",
  "arguments": {
    "model": "product.product",
    "ids": [1, 2, 3],
    "values": {
      "list_price": 150.00
    }
  }
}
```

## Troubleshooting

### Connection Issues
- **Error: "Connection refused"**
  - Check if the Odoo URL is correct
  - Ensure the server is accessible from your network
  - Verify firewall settings

### Authentication Failures
- **Error: "Authentication failed"**
  - Double-check username and password
  - Ensure the database name is correct
  - For Odoo 14+, try using an API key instead of password

### Permission Errors
- **Error: "Access Denied"**
  - User may not have permissions for the requested operation
  - Check user access rights in Odoo

### Timeout Issues
- Increase `ODOO_TIMEOUT` in your configuration
- Check network latency
- Consider reducing batch sizes for bulk operations

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Tools
To add a new tool:

1. Create a new class in `tools.py` inheriting from `BaseTool`
2. Implement `get_tool_definition()` and `execute()` methods
3. Add the tool to the server's tool map
4. Update the README with usage examples

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `ODOO_URL` | Odoo server URL | `http://localhost:8069` |
| `ODOO_DATABASE` | Database name | Required |
| `ODOO_USERNAME` | Username for authentication | Required* |
| `ODOO_PASSWORD` | Password for authentication | Required* |
| `ODOO_API_KEY` | API key for authentication (Odoo 14+) | Required* |
| `ODOO_TIMEOUT` | Request timeout in seconds | `30` |
| `ODOO_MAX_RETRIES` | Maximum retry attempts | `3` |
| `ODOO_RETRY_DELAY` | Delay between retries in seconds | `1.0` |

*Either password or API key is required

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.