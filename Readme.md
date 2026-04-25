# IxNetwork Inventory MCP Server

An MCP (Model Context Protocol) server that exposes IxNetwork chassis inventory, port management, and hardware telemetry as AI-callable tools. Connect it to any MCP-compatible agent or AI assistant to query and manage your Ixia chassis fleet using natural language.

Built with FastAPI. Every REST endpoint is automatically an MCP tool — no separate tool definitions. Runs as a Docker container with a volume-mounted credential store.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [MCP Client Setup](#mcp-client-setup)
- [MCP Tools Reference](#mcp-tools-reference)
- [Natural Language Query Examples](#natural-language-query-examples)
- [Managing Chassis at Runtime](#managing-chassis-at-runtime)
- [REST API Reference](#rest-api-reference)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Applying Code Changes](#applying-code-changes)

---

## Architecture

```
MCP Client / AI Agent
        │
        │  MCP over HTTP (Bearer token)
        ▼
┌───────────────────────────────┐
│   IxNetwork Inventory MCP     │  :8888
│                               │
│  FastAPI + fastapi-mcp        │
│  All routes = MCP tools       │
└──────────┬────────────────────┘
           │
           │  HTTPS REST (x-api-key)
           ▼
   IxNetwork Chassis(es)
   /chassis/api/v2/ixos/*

Credential Sources (priority order):
  1. External credentials service  →  http://host:3001/api/config/credentials
  2. config.json                   →  ./config.json (volume-mounted, writable)
```

Credentials are cached in memory for 60 seconds. The external credentials service is intended for integration with a separate inventory management application. If it is unavailable or not configured, the server falls back to `config.json` automatically.

---

## Prerequisites

- Docker and Docker Compose v2
- `openssl` (for API key generation)
- `npx` (for MCP client integration via `mcp-remote`)
- Network access to your IxNetwork chassis (HTTPS, port 443)

---

## Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd ixia-inventory-management-mcp
```

**2. Create `config.json` with your chassis credentials**

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

You can also add chassis later through any connected MCP client without editing this file — see [Managing Chassis at Runtime](#managing-chassis-at-runtime).

**3. Generate an API key**

```bash
export MCP_API_KEY=$(openssl rand -hex 32)
echo "MCP_API_KEY=$MCP_API_KEY" >> .env
echo "Save this key — you need it for your MCP client config"
```

**4. Start the server**

```bash
docker-compose up -d --build
```

**5. Verify it is running**

```bash
curl http://localhost:8888/health
# {"status":"ok"}

curl -H "Authorization: Bearer $MCP_API_KEY" http://localhost:8888/chassis/list
# ["10.36.237.131","10.36.236.121"]
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `MCP_API_KEY` | **Yes** | — | Bearer token for all API and MCP requests. Server will not start without this. |
| `MCP_SERVER_PORT` | No | `8888` | Port the server listens on. |
| `CREDENTIALS_SERVICE_URL` | No | `http://localhost:3001/api/config/credentials` | External credentials service endpoint. Ignored if unreachable. |
| `CREDENTIALS_SERVICE_TIMEOUT` | No | `5` | Seconds to wait before giving up on the credentials service. |

Set these in `.env` (picked up automatically by Docker Compose) or pass via `-e` flags to `docker run`.

### Credential Resolution

On each request (with 60-second caching), the server resolves credentials in this order:

1. **External credentials service** — `GET $CREDENTIALS_SERVICE_URL`. Expected response:
   ```json
   {
     "success": true,
     "credentials": [
       {"ip": "10.36.237.106", "username": "admin", "password": "admin"}
     ]
   }
   ```

2. **`config.json`** — fallback if service is unreachable or not configured.

Use `GET /credentials/status` (authenticated) to see which source is active and how stale the cache is.

### Docker Compose with Credentials Service

```bash
CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials \
  docker-compose up -d --build
```

On Linux, `host.docker.internal` resolves to the host gateway only with `extra_hosts` set — this is already present in `docker-compose.yml`.

### Rebuild vs Restart

| Change made | Action needed |
|---|---|
| Source code (`app.py`, etc.) | `docker-compose up -d --build` |
| `config.json` | None — volume-mounted. Call `POST /credentials/refresh` to apply within 60s, or wait for TTL. |
| Environment variables | `docker-compose up -d` (no rebuild needed) |

---

## MCP Client Setup

The server exposes a Streamable HTTP MCP endpoint at `http://localhost:8888/mcp`. Any MCP-compatible client can connect using `mcp-remote` as a bridge.

**Generic config (works with any client that accepts an `mcpServers` JSON block)**

```json
{
  "mcpServers": {
    "ixia-inventory": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://localhost:8888/mcp",
        "--header",
        "Authorization:Bearer YOUR_API_KEY_HERE"
      ]
    }
  }
}
```

Replace `YOUR_API_KEY_HERE` with the value of `$MCP_API_KEY`.

**Claude Code**

```bash
claude mcp add ixia-inventory -- npx mcp-remote@latest http://localhost:8888/mcp --header "Authorization:Bearer $MCP_API_KEY"
```

Or add the JSON block above to `~/.claude/settings.json` under the `mcpServers` key.

---

## MCP Tools Reference

All tools require a Bearer token passed via the `Authorization` header. The following tools are available:

### Inventory — Read

| Tool | Description | Required Input |
|---|---|---|
| `get_chassis_list` | Returns all configured chassis IPs. Use first to discover what is available. | None |
| `get_all_chassis_summary` | Queries all chassis in parallel. Use for a full lab snapshot. | None |
| `get_chassis_summary` | Hardware and software summary for one chassis. | `ip` |
| `get_chassis_cards` | Per-slot card details sorted by card number. | `ip` |
| `get_chassis_ports` | Port ownership, link state, and transceiver info. Includes aggregate free/owned counts. | `ip` |
| `get_chassis_sensors` | Temperature, voltage, and fan sensor readings. | `ip` |
| `get_chassis_performance` | Live CPU and memory utilization. Linux chassis only. | `ip` |
| `get_chassis_licensing` | License activation codes, expiry dates, and quantities. May take 10–20 seconds. | `ip` |
| `get_lldp_peer_data` | LLDP neighbors per port. Only ports with active peers are returned. Empty list = no peers discovered (not an error). | `ip` |

### Port Operations — Linux Chassis Only

| Tool | Description | Required Input |
|---|---|---|
| `take_port_ownership` | Reserves a port for test use. Check port is `Free` first with `get_chassis_ports`. | `ip`, `card_number`, `port_number` |
| `release_port_ownership` | Releases a port back to the free pool. | `ip`, `card_number`, `port_number` |
| `reboot_port` | Power-cycles the port ASIC. Port is unavailable for 10–30 seconds during reboot. | `ip`, `card_number`, `port_number` |

### Chassis Management

| Tool | Description | Required Input |
|---|---|---|
| `add_chassis_credentials` | Adds or updates a chassis. Persists to `config.json` and takes effect immediately. | `ip`, `username`, `password` |
| `remove_chassis_credentials` | Removes a chassis. Persists to `config.json` and takes effect immediately. | `ip` |
| `refresh_credentials` | Forces a reload from the credentials service or `config.json`, bypassing the 60-second cache. | None |
| `get_credentials_status` | Returns the active credential source and cache age. No network call made. | None |

### Tool Response Conventions

- All responses include `lastUpdatedAt_UTC` (format: `MM/DD/YYYY, HH:MM:SS` UTC).
- Unreachable chassis return `chassisStatus: "Not Reachable"` with remaining fields as `"NA"`. Tools do not raise errors for unreachable chassis.
- Port operations return HTTP 404 if the card/port number does not exist, and HTTP 502 if the chassis rejects the operation (e.g., port already owned).
- Windows chassis have `os: "Windows"` and return `"NA"` for `mem_bytes` and `cpu_pert_usage` — performance counters are not available on that platform.

---

## Natural Language Query Examples

Example natural language queries once your MCP client is connected.

**Discovery**
```
List all chassis in the lab.
Give me a health summary of the entire lab.
What IxOS version is running on 10.36.237.131?
```

**Hardware inspection**
```
Show me all cards in chassis 10.36.237.131.
How many ports are free on 10.36.236.121?
Who owns port 1/3 on chassis 10.36.237.131?
What transceivers are installed on chassis 10.36.237.131?
What is the temperature of chassis 10.36.237.131?
```

**Performance and licensing**
```
What is the CPU and memory usage on 10.36.237.131?
Show me the license expiry dates for chassis 10.36.237.131.
Are any licenses expired across all chassis?
```

**Topology**
```
What device is connected to port 1/1 on chassis 10.36.237.131?
Show me the LLDP neighbors for chassis 10.36.237.131.
```

**Port operations**
```
Take ownership of port 1/1 on chassis 10.36.237.131.
Release port 2/3 on chassis 10.36.236.121.
Reboot port 1/4 on 10.36.237.131.
```

**Chassis management**
```
Add chassis 10.36.237.200 with username admin and password admin123.
Remove chassis 10.36.237.131 from the system.
Refresh the chassis credentials.
Which credential source is currently active?
```

---

## Managing Chassis at Runtime

Chassis can be added, updated, or removed while the server is running — no restart required. Changes persist to `config.json` and are reflected immediately in all subsequent tool calls.

**Add or update a chassis**

Via MCP agent: *"Add chassis 10.36.237.200 with username admin and password admin123"*

Via curl:
```bash
curl -X POST http://localhost:8888/chassis/credentials \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ip": "10.36.237.200", "username": "admin", "password": "admin123"}'
```

**Remove a chassis**

Via MCP agent: *"Remove chassis 10.36.237.200"*

Via curl:
```bash
curl -X POST http://localhost:8888/chassis/credentials/remove \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ip": "10.36.237.200"}'
```

**Credentials service note**: If an external credentials service is configured, it takes precedence over `config.json` on each 60-second cache refresh. Chassis added through these tools are written to `config.json` and are available immediately in memory, but will not appear in responses after a cache refresh if the credentials service does not include them. To use these tools as your primary source of truth, do not configure `CREDENTIALS_SERVICE_URL`.

---

## REST API Reference

All endpoints require `Authorization: Bearer <MCP_API_KEY>` except `GET /health`.

### Inventory

| Method | Endpoint | Body | Description |
|---|---|---|---|
| GET | `/health` | — | Health check. No auth required. Returns `{"status":"ok"}`. |
| GET | `/chassis/list` | — | All configured chassis IPs. |
| GET | `/chassis/all/summary` | — | Summary for all chassis, fetched in parallel. |
| POST | `/chassis/summary` | `{"ip":"..."}` | Hardware summary for one chassis. |
| POST | `/chassis/cards` | `{"ip":"..."}` | Card details. |
| POST | `/chassis/ports` | `{"ip":"..."}` | Port details with ownership and link state. |
| POST | `/chassis/sensors` | `{"ip":"..."}` | Sensor readings. |
| POST | `/chassis/performance` | `{"ip":"..."}` | CPU and memory utilization. |
| POST | `/chassis/licensing` | `{"ip":"..."}` | License activation details. |
| POST | `/chassis/lldp` | `{"ip":"..."}` | LLDP neighbor data. |

### Port Operations

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/chassis/take_port_ownership` | `{"ip":"...","card_number":1,"port_number":1}` | Take port ownership. |
| POST | `/chassis/release_port_ownership` | `{"ip":"...","card_number":1,"port_number":1}` | Release port ownership. |
| POST | `/chassis/reboot_port` | `{"ip":"...","card_number":1,"port_number":1}` | Reboot a port. |

### Chassis Credential Management

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/chassis/credentials` | `{"ip":"...","username":"...","password":"..."}` | Add or update a chassis. |
| POST | `/chassis/credentials/remove` | `{"ip":"..."}` | Remove a chassis. |

### Credential Service

| Method | Endpoint | Body | Description |
|---|---|---|---|
| GET | `/credentials/status` | — | Cache age, active source, chassis IPs. No network call. |
| POST | `/credentials/refresh` | — | Force reload from service or `config.json`. |

Full interactive documentation: `http://localhost:8888/docs`

---

## Troubleshooting

### Server will not start

**Symptom**: Container exits immediately.

**Cause**: `MCP_API_KEY` is not set.

```bash
docker-compose logs ixnetwork-mcp-server
# RuntimeError: MCP_API_KEY environment variable is required but not set.
```

**Fix**:
```bash
export MCP_API_KEY=$(openssl rand -hex 32)
docker-compose up -d
```

---

### 401 Unauthorized on all requests

**Symptom**: Every curl or MCP client call returns `401`.

**Cause**: Mismatched API key between the server and the client.

**Diagnosis**:
```bash
# Verify the server accepted the key at startup
docker-compose logs ixnetwork-mcp-server | head -20

# Test with the exact key the server has
docker exec ixnetwork-inventory-mcp env | grep MCP_API_KEY
curl -H "Authorization: Bearer <that_key>" http://localhost:8888/chassis/list
```

**Fix**: Ensure your MCP client config passes the same key that was passed to the container via `--header "Authorization:Bearer <key>"`.

---

### MCP client shows no tools / server not connected

**Symptom**: Tool list is empty or the server fails to connect.

**Diagnosis steps**:

1. Confirm the server is reachable:
   ```bash
   curl http://localhost:8888/health
   ```

2. Confirm `npx` and `mcp-remote` are available:
   ```bash
   npx mcp-remote@latest http://localhost:8888/mcp --header "Authorization:Bearer $MCP_API_KEY"
   ```

3. Check your MCP client config for JSON syntax errors — invalid JSON silently prevents loading.

4. Restart your MCP client fully after any config change.

---

### Chassis shows "Not Reachable"

**Symptom**: `get_chassis_summary` returns `chassisStatus: "Not Reachable"` for a chassis.

**Cause**: Network connectivity, wrong credentials, or the chassis REST service is down.

**Diagnosis**:
```bash
# Test chassis reachability from the host
curl -k https://10.36.237.131/chassis/api/v2/ixos/chassis

# Test from inside the container
docker exec ixnetwork-inventory-mcp \
  curl -k https://10.36.237.131/chassis/api/v2/ixos/chassis

# Verify credentials are correct
curl -H "Authorization: Bearer $MCP_API_KEY" http://localhost:8888/credentials/status
```

If the container cannot reach the chassis but the host can, check Docker network mode and firewall rules.

---

### Credentials service not being used

**Symptom**: `GET /credentials/status` shows `credentials_service_available: false` even though the service is running.

**Cause**: When running in Docker, `localhost` inside the container refers to the container itself — not the host.

**Fix**: Use `host.docker.internal` in the URL:
```bash
CREDENTIALS_SERVICE_URL=http://host.docker.internal:3001/api/config/credentials \
  docker-compose up -d
```

On Linux, this also requires the `extra_hosts` entry in `docker-compose.yml` (already present).

**Verify the service response format**:
```bash
curl http://localhost:3001/api/config/credentials
```
The response must include `"success": true` and a `"credentials"` array with `ip`, `username`, `password` fields. Any deviation causes the server to fall back to `config.json`.

---

### Port operation fails with 502

**Symptom**: `take_port_ownership` or `release_port_ownership` returns HTTP 502.

**Cause**: The chassis rejected the operation. Common reasons:
- Port is already owned by another user or test session.
- The chassis is Windows-based (port operations are Linux-only).
- The IxOS REST service on the chassis returned an error.

**Diagnosis**:
```bash
# Check current port ownership before operating
curl -X POST http://localhost:8888/chassis/ports \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ip": "10.36.237.131"}'
```

Look at the `owner` field for the target port. If it is not `"Free"`, the port must be released by its current owner first.

---

### View logs

```bash
# Follow live logs
docker-compose logs -f

# Filter for errors only
docker-compose logs | grep '"levelname": "ERROR"'

# Trace a specific request by correlation ID
docker-compose logs | grep '"request_id": "abc123"'
```

All log lines are JSON. Each request generates a unique `request_id`. If your MCP client surfaces an error, find the corresponding `request_id` in the `X-Request-ID` response header (visible in browser devtools or curl `-v` output) and grep for it in logs.

---

## Development

### Local setup

```bash
pip install -r requirements.txt
export MCP_API_KEY=dev-secret
python app.py
```

The server starts on port 8888 by default. Set `MCP_SERVER_PORT` to override.

### Running tests

```bash
pytest tests/ -v
```

Tests are fully mocked — no real chassis required. `tests/test_caller_modifier.py` covers the IxOS data transformation layer. `tests/test_credentials_crud.py` covers the credential CRUD endpoints using `FastAPI TestClient` with a temporary `config.json`.

### Project structure

```
app.py                      # FastAPI application and all MCP-exposed endpoints
IxOSRestCallerModifier.py   # Data transformation layer (session → structured dict)
RestApi/
  IxOSRestInterface.py      # Low-level HTTP client for IxOS REST API
config.json                 # Chassis credentials (volume-mounted, writable)
tests/
  conftest.py               # Shared fixtures with mock IxRestSession objects
  test_caller_modifier.py   # Unit tests for IxOSRestCallerModifier
  test_credentials_crud.py  # Integration tests for credential CRUD endpoints
docker-compose.yml
Dockerfile
requirements.txt
```

### Adding a new MCP tool

1. Add a route to `app.py` with a descriptive `operation_id`. That string becomes the MCP tool name.
2. Write an AI-oriented docstring: what the tool returns (field names), when to use it versus other tools, an example input.
3. Raise `HTTPException` for error conditions — do not return `{"success": false}` with HTTP 200.
4. Add business logic to `IxOSRestCallerModifier.py` if it involves IxOS data transformation.
5. Rebuild: `docker-compose up -d --build`

---

## Applying Code Changes

The server runs inside Docker. How you pick up a change depends on what you changed.

### Quick reference

| What changed | Command needed | MCP client reconnect? |
|---|---|---|
| Source code (`app.py`, `IxOSRestCallerModifier.py`, `RestApi/`, `Dockerfile`, `requirements.txt`) | `docker-compose up -d --build` | **Yes** |
| `config.json` (chassis credentials) | `curl -X POST http://localhost:8888/credentials/refresh -H "Authorization: Bearer $MCP_API_KEY"` — or wait 60 s for auto-refresh | No |
| Environment variables (`.env`) | `docker-compose up -d` | No |

### Source code changes (rebuild required)

Any change to Python source files requires rebuilding the container image:

```bash
docker-compose up -d --build
```

This stops the old container, rebuilds the image from the `Dockerfile`, and starts a fresh container. The server is unavailable for a few seconds during the restart.

**After a rebuild, reconnect your MCP client.** The MCP tool list is served at startup — stale client connections will not see new or changed tools. How to reconnect:

- **Claude Desktop / Claude Code**: Run `claude mcp restart ixia-inventory` or restart the client application entirely.
- **Any `mcp-remote` bridge**: Kill the `mcp-remote` process and let your client relaunch it. The bridge re-fetches the tool manifest on connect.
- **Verify** the new tool is visible by asking your agent: *"What tools do you have available?"*

### config.json changes (no rebuild)

`config.json` is volume-mounted into the container — the file on disk is read directly. No rebuild or restart is needed. Force an immediate reload with:

```bash
curl -X POST http://localhost:8888/credentials/refresh \
  -H "Authorization: Bearer $MCP_API_KEY"
```

Without this call, the new credentials will be picked up automatically within 60 seconds (the in-memory cache TTL).

### Environment variable changes (restart only)

Changes to `.env` are picked up with a plain restart — no image rebuild:

```bash
docker-compose up -d
```
