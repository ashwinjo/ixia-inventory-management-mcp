# IxNetwork Inventory API with MCP Integration

This is a modernized FastAPI application that provides IxNetwork chassis inventory and metrics through a REST API with Model Context Protocol (MCP) integration.

## Features

- FastAPI-based REST API
- MCP integration for AI assistant compatibility
- Real-time chassis information retrieval
- Comprehensive API documentation
- Error handling and fallbacks

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The server will start at http://localhost:8000

## API Documentation

Once running, you can access:
- REST API docs: http://localhost:8000/docs
- MCP endpoint: http://localhost:8000/mcp

## Connecting with Claude Desktop

Add the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ixnetwork-inventory": {
      "command": "/path/to/mcp-proxy",
      "args": ["http://localhost:8000/mcp"]
    }
  }
}
```

Replace `/path/to/mcp-proxy` with the actual path to your mcp-proxy executable (find it using `which mcp-proxy`).

## Available Endpoints

1. GET `/chassis/summary`
   - Get chassis summary information
   - Operation ID: mcp_get_chassis_summary

2. GET `/chassis/cards`
   - Get chassis cards information
   - Operation ID: mcp_get_chassis_cards

3. GET `/chassis/ports`
   - Get chassis ports information
   - Operation ID: mcp_get_chassis_ports

## Error Handling

The API includes graceful error handling:
- Connection failures return "NA" values instead of errors
- All endpoints include proper error responses
- Timestamps are included in responses

## Security Notes

- Credentials are passed per-request for security
- No credentials are stored in the application
- HTTPS is recommended for production deployment
