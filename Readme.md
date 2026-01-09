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
- **Credentials Service Integration**: Fetch credentials from external service with automatic fallback
- **Health Monitoring**: Built-in health checks and error handling
- **Graceful Fallbacks**: Robust error handling with "NA" responses for unreachable chassis
- **Containerized Deployment**: Docker and Docker Compose ready

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI Server │    │  IxNetwork API  │
│   (Templates)   │◄──►│   (Port 8888)    │◄──►│   (REST Calls)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │  │
                              │  │
          ┌───────────────────┘  └───────────────────┐
          ▼                                          ▼
   ┌──────────────────┐                    ┌──────────────────┐
   │   MCP Server     │                    │ Credentials      │
   │ (AI Integration) │                    │ Service (:3001)  │
   └──────────────────┘                    │    or            │
                                           │ config.json      │
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

You have **two options** for configuring chassis credentials:

#### Option A: External Credentials Service (Recommended)
If you have a credentials service running, the system will automatically fetch credentials from it:

```
Service URL: http://localhost:3001/api/config/credentials
```

Expected response format:
```json
{
  "success": true,
  "count": 2,
  "credentials": [
    {
      "ip": "10.36.237.106",
      "username": "admin",
      "password": "admin"
    },
    {
      "ip": "10.36.75.163",
      "username": "admin",
      "password": "admin"
    }
  ]
}
```

#### Option B: Local Config File (Fallback)
If the credentials service is unavailable, the system falls back to `config.json`:
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

> **Note**: The system automatically tries the credentials service first, then falls back to config.json if unavailable.

### 3. Run with Docker (Recommended)

#### Using Docker Compose (Simplest)

**Without credentials service** (uses config.json only):
```bash
docker-compose up -d --build
```

**With credentials service** (recommended):
```bash
# Edit docker-compose.yml and uncomment/set CREDENTIALS_SERVICE_URL
# OR use environment variable override:
CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials docker-compose up -d --build
```

#### Using Docker Run

**Build the image:**
```bash
docker build -t ixnetwork-mcp-server-image .
```

**Run WITHOUT credentials service** (uses config.json):
```bash
docker run -d \
  --name ixnetwork-inventory-mcp \
  -p 8888:8888 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -e PYTHONUNBUFFERED=1 \
  -e MCP_SERVER_PORT=8888 \
  --restart unless-stopped \
  ixnetwork-mcp-server-image
```

**Run WITH credentials service** (recommended):
```bash
docker run -d \
  --name ixnetwork-inventory-mcp \
  -p 8888:8888 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -e PYTHONUNBUFFERED=1 \
  -e MCP_SERVER_PORT=8888 \
  -e CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials \
  -e CREDENTIALS_SERVICE_TIMEOUT=5 \
  --add-host=host.docker.internal:host-gateway \
  --restart unless-stopped \
  ixnetwork-mcp-server-image
```

> **⚠️ Important**: 
> - You need to have `config.json` file in `$(pwd)` as a fallback
> - Use `host.docker.internal` to access services running on the host machine from within the container
> - The `--add-host=host.docker.internal:host-gateway` flag enables host access on Linux

#### Quick Reference

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
| `/chassis/lldp` | POST | Get LLDP peer data | `get_lldp_peer_data` |

### Credentials Management Endpoints

| Endpoint | Method | Description | MCP Operation ID |
|----------|--------|-------------|------------------|
| `/credentials/refresh` | POST | Force refresh credentials from service | `refresh_credentials` |
| `/credentials/status` | GET | Get credentials source status | `get_credentials_status` |

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
- **Credentials Service**: Primary source for credentials (if available)
- **External Config**: `./config.json` is mounted into container as fallback
- **Hot Reload**: Credentials from service are cached for 60 seconds (auto-refresh)
- **Manual Refresh**: Call `/credentials/refresh` to force reload
- **Security**: Read-only mount prevents container modification of config.json

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

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Ensures Python output is not buffered |
| `MCP_SERVER_PORT` | `8888` | MCP server port |
| `CREDENTIALS_SERVICE_URL` | `http://localhost:3001/api/config/credentials` | URL of the external credentials service |
| `CREDENTIALS_SERVICE_TIMEOUT` | `5` | Timeout in seconds for credentials service requests |

### Passing Environment Variables at Runtime

#### With Docker Run
```bash
docker run -d \
  -e CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials \
  -e CREDENTIALS_SERVICE_TIMEOUT=10 \
  --add-host=host.docker.internal:host-gateway \
  ... other options ...
  ixnetwork-mcp-server-image
```

#### With Docker Compose
**Option 1**: Edit `docker-compose.yml` directly:
```yaml
environment:
  - CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials
  - CREDENTIALS_SERVICE_TIMEOUT=5
```

**Option 2**: Create a `.env` file in the same directory:
```bash
# .env file
CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials
CREDENTIALS_SERVICE_TIMEOUT=5
```

Then update `docker-compose.yml`:
```yaml
environment:
  - CREDENTIALS_SERVICE_URL=${CREDENTIALS_SERVICE_URL}
  - CREDENTIALS_SERVICE_TIMEOUT=${CREDENTIALS_SERVICE_TIMEOUT:-5}
```

**Option 3**: Pass at runtime:
```bash
CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials docker-compose up -d
```

### Credentials Service Integration

The system uses a **service-first, fallback-to-file** approach:

```
┌─────────────────────┐     ┌─────────────────────┐
│  Credentials        │     │    config.json      │
│  Service            │     │    (fallback)       │
│  :3001/api/config/  │     │                     │
│  credentials        │     │                     │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          │  1. Try first              │  2. Fallback
          │                            │
          ▼                            ▼
┌─────────────────────────────────────────────────┐
│              MCP Server (app.py)                │
│                                                 │
│  • 60-second credential caching                 │
│  • Automatic retry on service failure           │
│  • Graceful fallback to config.json             │
└─────────────────────────────────────────────────┘
```

#### Verifying Credentials Source

Check which source credentials are coming from:
```bash
curl http://localhost:8888/credentials/status
```

Response when using credentials service:
```json
{
  "credentials_service_url": "http://localhost:3001/api/config/credentials",
  "credentials_service_available": true,
  "credentials_service_timeout": 5,
  "cache_ttl_seconds": 60,
  "cache_age_seconds": 15.23,
  "cache_valid": true,
  "chassis_count": 2,
  "chassis_ips": ["10.36.237.106", "10.36.75.163"]
}
```

Force refresh credentials:
```bash
curl -X POST http://localhost:8888/credentials/refresh
```

Response when refreshing from credentials service:
```json
{
  "success": true,
  "source": "credentials_service",
  "service_url": "http://localhost:3001/api/config/credentials",
  "chassis_count": 2,
  "chassis_ips": ["10.36.237.106", "10.36.75.163"],
  "message": "Credentials refreshed from credentials service"
}
```

Response when falling back to config.json:
```json
{
  "success": true,
  "source": "config.json",
  "service_url": "http://localhost:3001/api/config/credentials",
  "service_available": false,
  "chassis_count": 2,
  "chassis_ips": ["10.36.237.106", "10.36.75.163"],
  "message": "Credentials loaded from config.json (credentials service unavailable)"
}
```

### ⚠️ Applying Code Changes (Important!)

If you've made changes to `app.py` or any other source files, you **must rebuild the Docker container** for the changes to take effect.

#### Using Docker Compose
```bash
# Rebuild and restart the container
docker-compose up -d --build
```

#### Using Docker Run
```bash
# Stop and remove the old container
docker stop ixnetwork-inventory-mcp
docker rm ixnetwork-inventory-mcp

# Rebuild the image with new code
docker build -t ixnetwork-mcp-server-image .

# Run the new container
docker run -d \
  --name ixnetwork-inventory-mcp \
  -p 8888:8888 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -e PYTHONUNBUFFERED=1 \
  -e CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials \
  --add-host=host.docker.internal:host-gateway \
  --restart unless-stopped \
  ixnetwork-mcp-server-image
```

#### Verify New Endpoints Are Available
After rebuilding, check the API documentation to confirm all endpoints are available:
```bash
# Open in browser
open http://localhost:8888/docs

# Or test the credentials endpoints directly
curl http://localhost:8888/credentials/status
curl -X POST http://localhost:8888/credentials/refresh
```

> **Note**: Changes to `config.json` do NOT require a rebuild since it's mounted as a volume. However, credentials are cached for 60 seconds, so call `/credentials/refresh` to force reload immediately.

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

- **Credential Management**: Credentials fetched from secure credentials service, with local config fallback
- **Credentials Caching**: Credentials cached in memory for 60 seconds to reduce service load
- **Network Security**: Use VPN for chassis access
- **Container Security**: Non-root user in container
- **API Security**: Consider adding authentication for production
- **Service Communication**: Use HTTPS for credentials service in production

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

## 🔧 Troubleshooting

### Endpoints Not Found (404)

**Problem**: New endpoints like `/credentials/status` return 404.

**Solution**: Rebuild the Docker container to pick up code changes:
```bash
docker-compose up -d --build
```

### Credentials Service Not Connecting

**Problem**: Credentials always fall back to `config.json` even though the service is running.

**Solutions**:
1. **Check the service URL**: Ensure `CREDENTIALS_SERVICE_URL` points to the correct address
2. **Use host.docker.internal**: When running in Docker, use `http://host.docker.internal:3001/...` instead of `http://localhost:3001/...`
3. **Add host mapping** (Linux): Include `--add-host=host.docker.internal:host-gateway` in your docker run command
4. **Check service response format**: The service must return:
   ```json
   {
     "success": true,
     "credentials": [{"ip": "x.x.x.x", "username": "...", "password": "..."}]
   }
   ```

### View Container Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker Run
docker logs -f ixnetwork-inventory-mcp
```

### Check If Container Is Running

```bash
docker ps | grep ixnetwork
```

### Test Credentials Service Directly

```bash
# From host machine
curl http://localhost:3001/api/config/credentials

# From inside container (if needed)
docker exec ixnetwork-inventory-mcp curl http://host.docker.internal:3001/api/config/credentials
```

---

**Built with ❤️ for Ixia administrators and AI enthusiasts**