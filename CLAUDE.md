# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Local development
pip install -r requirements.txt
python app.py
uvicorn app:app --reload --host 0.0.0.0 --port 8888

# Docker (primary deployment method)
docker-compose up -d --build   # rebuild after any source file change
docker-compose logs -f
docker-compose down

# Force credentials refresh (no rebuild needed for config.json changes)
curl -X POST http://localhost:8888/credentials/refresh

# Check which credential source is active
curl http://localhost:8888/credentials/status
```

After code changes, always rebuild: `docker-compose up -d --build`. Changes to `config.json` only require a credentials refresh since it is volume-mounted read-only.

## Architecture

**Entry point**: `app.py` — a FastAPI app that auto-exposes all routes as MCP tools via `fastapi-mcp`. The `operation_id` on each route becomes the MCP tool name. No separate MCP tool definitions exist; adding a FastAPI route with an `operation_id` is sufficient.

**IxOS REST layer** (two files, keep them separate):
- `RestApi/IxOSRestInterface.py` — `IxRestSession`: low-level HTTP wrapper. Authenticates via `POST /platform/api/v1/auth/session` to get an API key, then passes `x-api-key` header on all calls to `https://<chassis>/chassis/api/v2/ixos/*`. Handles async 202 polling. Port/card operations (take ownership, reboot, hotswap) are Linux chassis only.
- `IxOSRestCallerModifier.py` — business logic layer. Takes a session and returns structured dicts/lists. All data normalization, field filtering, and "NA" fallbacks live here.

**Credential resolution** (in `app.py`):
1. Try `CREDENTIALS_SERVICE_URL` (default: `http://localhost:3001/api/config/credentials`) — expects `{"success": true, "credentials": [{"ip", "username", "password"}]}`
2. Fall back to `config.json` (format: `{"<ip>": {"username": "...", "password": "..."}}`)
3. Results cached in-memory for 60s. On file fallback, cache timestamp is set to `now - 30s` so the service is retried sooner.

**Windows vs Linux chassis detection**: `get_chassis_information()` infers OS type by whether `/perfcounters` returns data. Windows chassis do not expose perf counters. Port operations (`take_ownership`, `release_port_ownership`, `reboot_port`) are only valid on Linux chassis.

**Port operation flow**: card/port numbers → `session.get_ports(params={'cardNumber': N, 'portNumber': M})` → internal `id` → POST to `/ports/<id>/operations/<action>`.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `CREDENTIALS_SERVICE_URL` | `http://localhost:3001/api/config/credentials` | External credentials source |
| `CREDENTIALS_SERVICE_TIMEOUT` | `5` | Seconds before giving up on service |
| `MCP_SERVER_PORT` | `8888` | Server port |

When running in Docker and the credentials service is on the host, use `http://host.docker.internal:3001/...` and add `--add-host=host.docker.internal:host-gateway` (Linux hosts only).

## Claude Desktop MCP Integration

```json
{
  "mcpServers": {
    "ixia-inventory": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8888/mcp"]
    }
  }
}
```

## Chassis Credential CRUD (runtime, no restart needed)

`POST /chassis/credentials` (`add_chassis_credentials`) — adds or updates a chassis. Writes directly to `config.json` via `save_credentials_to_file()` then patches `_credentials_cache`. Takes effect immediately. Direct write (not tmp+rename) is intentional — Docker file bind mounts do not reliably propagate renames to the host file.

`POST /chassis/credentials/remove` (`remove_chassis_credentials`) — removes a chassis by IP. Same atomic write + cache patch pattern.

Both endpoints acquire `_cache_lock` for the entire read-modify-write cycle to prevent concurrent mutation races.

`config.json` is mounted **writable** (no `:ro`) in Docker so container can persist changes to the host file.

## Auth

All endpoints except `GET /health` require `Authorization: Bearer <MCP_API_KEY>`. Enforced by the single `request_middleware` in `app.py`. `MCP_API_KEY` env var is required at startup — server raises `RuntimeError` if unset.

## Adding New Endpoints

1. Define route in `app.py` with a unique `operation_id` — it becomes the MCP tool name automatically
2. Add business logic in `IxOSRestCallerModifier.py` (keep transport/logic separated)
3. Raise `HTTPException` for errors (not `return {"success": false}`) — port ops raise 404/502
4. Write AI-oriented docstring: what it returns (field names), when to use vs other tools, example input
5. Rebuild container: `docker-compose up -d --build`
