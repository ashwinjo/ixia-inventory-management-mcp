# 🚀 IxNetwork Inventory Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-00D4AA?style=for-the-badge)](https://modelcontextprotocol.io/)

> **Enterprise-grade IxNetwork chassis inventory and monitoring system with AI assistant integration**

A comprehensive FastAPI-based solution for managing IxNetwork chassis inventory, providing real-time monitoring, performance metrics, and seamless integration with AI assistants through the Model Context Protocol (MCP).

## 🌟 Key Features

### 🔧 **Core Functionality**
- **Real-time Chassis Monitoring**: Live inventory and status tracking
- **Comprehensive Hardware Details**: Cards, ports, sensors, and licensing information
- **Performance Metrics**: CPU, memory utilization, and system health
- **Multi-Chassis Support**: Manage multiple IxNetwork chassis simultaneously
- **RESTful API**: Full-featured REST API with automatic documentation

### 🤖 **AI Integration**
- **MCP (Model Context Protocol) Support**: Direct integration with Claude Desktop and other AI assistants
- **Streaming Support**: Real-time data streaming capabilities
- **Intelligent Querying**: Natural language interface for inventory queries

### 🛡️ **Enterprise Features**
- **Secure Configuration Management**: External config file mounting with Docker
- **Health Monitoring**: Built-in health checks and error handling
- **Graceful Fallbacks**: Robust error handling with "NA" responses for unreachable chassis
- **Containerized Deployment**: Docker and Docker Compose ready

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI Server │    │  IxNetwork API  │
│   (Templates)   │◄──►│   (Port 8888)    │◄──►│   (REST Calls)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   MCP Server     │
                       │ (AI Integration) │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- IxNetwork chassis access

### 1. Clone and Setup
```bash
git clone <repository-url>
cd IxInventoryManagement
```

### 2. Configure Chassis Access
Edit `config.json` with your chassis credentials:
```json
{
  "10.36.237.131": {
    "username": "admin",
    "password": "your_password"
  },
  "10.36.236.121": {
    "username": "admin", 
    "password": "your_password"
  }
}
```

### 3. Run with Docker (Recommended)


> If you make changes and want to build and run:

```bash
docker-compose up -d --build 
``
OR 

``
docker build -t ixnetwork-mcp-server-image .
```

```bash
docker run -d \
  --name ixnetwork-inventory-mcp \
  -p 8888:8888 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -e PYTHONUNBUFFERED=1 \
  -e MCP_SERVER_PORT=8888 \
  --restart unless-stopped \
  ixnetwork-mcp-server-image

  *** You need to have config.json file in $(pwd)
```

If you want to just run the container with no changes as such. ``` bash`docker-compose up -d  ```

Difference:

| Command                        | Rebuild Image? | When to Use                                       |
| ------------------------------ | -------------- | ------------------------------------------------- |
| `docker-compose up -d`         | ❌ No           | Just running containers, no Dockerfile changes    |
| `docker-compose up -d --build` | ✅ Yes          | Any time you modify files used in the image build |



### How to add/delete/update chassis information
```bash
1. Go to the folder from where you run the container
2. Modify config.json
3. Changes should get reflected in you mcp tool calls
```



### 4. Access the System
- **API Documentation**: http://localhost:8888/docs
- **MCP Endpoint**: http://localhost:8888/mcp
- **Health Check**: http://localhost:8888/docs

## 🤝 API Endpoints

### Core Inventory Endpoints

| Endpoint | Method | Description | MCP Operation ID |
|----------|--------|-------------|------------------|
| `/chassis/summary` | POST | Get chassis hardware details | `get_chassis_summary` |
| `/chassis/cards` | POST | Get card information | `get_chassis_cards` |
| `/chassis/ports` | POST | Get port information | `get_chassis_ports` |
| `/chassis/sensors` | POST | Get sensor data | `get_chassis_sensors` |
| `/chassis/licensing` | POST | Get license information | `get_chassis_licensing` |
| `/chassis/performance` | POST | Get performance metrics | `get_chassis_performance` |
| `/chassis/list` | GET | List all configured chassis | `get_chassis_list` |

### Request Format
```json
{
  "ip": "10.36.237.131"
}
```

### Response Example
```json
{
  "chassisIp": "10.36.237.131",
  "chassisSerial#": "123456789",
  "controllerSerial#": "987654321",
  "chassisType": "XGS12-SD",
  "physicalCards#": 12,
  "chassisStatus": "Ready",
  "lastUpdatedAt_UTC": "12/15/2023, 14:30:25",
  "mem_bytes": 8589934592,
  "mem_bytes_total": 17179869184,
  "cpu_pert_usage": 15.2,
  "os": "Linux",
  "IxOS": "9.20.2212.15",
  "IxNetwork Protocols": "9.20.2212.15",
  "IxOS REST": "9.20.2212.15"
}
```

## 🤖 AI Assistant Integration

### Claude Desktop Setup
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ixia-inventory": {
            "command": "npx",
            "args": [
                "mcp-remote",
                "http://localhost:8888/mcp"
            ]
        }
  }
}
```

### Example AI Queries
- "Show me all chassis cards for 10.36.237.131"
- "What's the performance of chassis 10.36.236.121?"
- "List all available chassis"
- "Get sensor data for the first chassis"

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down
```

### Configuration Management
- **External Config**: `./config.json` is mounted into container
- **Hot Reload**: Changes to config.json require container restart
- **Security**: Read-only mount prevents container modification

## 📁 Project Structure

```
IxInventoryManagement/
├── app.py                          # Main FastAPI application
├── config.json                     # Chassis credentials
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── IxOSRestCallerModifier.py     # IxNetwork API wrapper
├── RestApi/
│   └── IxOSRestInterface.py      # REST API interface
├── app/
│   ├── templates/                 # Web interface templates
│   │   ├── chassisDetails.html
│   │   ├── chassisCardsDetails.html
│   │   ├── chassisPortDetails.html
│   │   ├── chassisSensorsDetails.html
│   │   ├── chassisLicenseDetails.html
│   │   ├── chassisPerformanceMetrics.html
│   │   └── upload.html
│   └── static/                    # Static assets
│       ├── css/
│       ├── js/
│       └── assets/
└── logs/                          # Application logs
```

## 📄 Configuration

### Environment Variables
- `PYTHONUNBUFFERED=1`: Ensures Python output is not buffered
- `MCP_SERVER_PORT=8888`: MCP server port

### Health Checks
- **Endpoint**: `http://localhost:8888/docs`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Run with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8888
```

### Adding New Endpoints
1. Define the endpoint in `app.py`
2. Add MCP operation ID
3. Update documentation
4. Test with Docker

## 🔒 Security Considerations

- **Credential Management**: Credentials stored in external config file
- **Network Security**: Use VPN for chassis access
- **Container Security**: Non-root user in container
- **API Security**: Consider adding authentication for production

## 📈 Monitoring & Logging

- **Structured Logging**: Comprehensive debug logging
- **Error Handling**: Graceful fallbacks for unreachable chassis
- **Health Monitoring**: Built-in health checks
- **Performance Tracking**: Real-time metrics collection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: http://localhost:8888/docs
- **Issues**: Create an issue in the repository
- **MCP Documentation**: [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Built with ❤️ for Ixia administrators and AI enthusiasts**