from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
from RestApi.IxOSRestInterface import IxRestSession
import IxOSRestCallerModifier as ixOSRestCaller

import asyncio
import contextvars
import ipaddress
import logging
import json
import os
import requests
import threading
import time
import uuid
from datetime import datetime

# ── Structured JSON Logging ──────────────────────────────────────────────────

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def _setup_logging() -> None:
    try:
        from pythonjsonlogger import jsonlogger
        handler = logging.StreamHandler()
        handler.setFormatter(
            jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s"
            )
        )
        handler.addFilter(_CorrelationIdFilter())
        root = logging.getLogger()
        root.handlers = []
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    except ImportError:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().warning(
            "python-json-logger not installed; using plain logging. "
            "Run: pip install python-json-logger"
        )


_setup_logging()
logger = logging.getLogger(__name__)

# ── Startup Validation ───────────────────────────────────────────────────────

MCP_API_KEY: str = os.environ.get("MCP_API_KEY", "")
if not MCP_API_KEY:
    raise RuntimeError(
        "MCP_API_KEY environment variable is required but not set. "
        "Generate one with: openssl rand -hex 32"
    )

# ── Credentials Service Configuration ───────────────────────────────────────

CREDENTIALS_SERVICE_URL = os.environ.get(
    "CREDENTIALS_SERVICE_URL",
    "http://localhost:3001/api/config/credentials"
)
CREDENTIALS_SERVICE_TIMEOUT = int(os.environ.get("CREDENTIALS_SERVICE_TIMEOUT", "5"))

# ── Thread-Safe Credentials Cache ───────────────────────────────────────────

_cache_lock = threading.Lock()
_credentials_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": 0,
    "ttl": 60,
    "last_source": None,  # "service" | "file" | None
}

# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="IxNetwork Inventory API",
    description="API for managing IxNetwork chassis inventory and metrics",
    version="1.0.0"
)

# ── Request Middleware (correlation ID + auth) ───────────────────────────────

_AUTH_EXCLUDED_PATHS = {"/health"}


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Sets correlation ID and enforces Bearer token auth on all routes except /health."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(request_id)
    try:
        if request.url.path not in _AUTH_EXCLUDED_PATHS:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.warning("Request missing Authorization header", extra={"path": str(request.url.path)})
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing Authorization header. Use: Authorization: Bearer <api_key>"},
                    headers={"X-Request-ID": request_id},
                )
            api_token = auth_header.split(" ", 1)[1]
            if api_token != MCP_API_KEY:
                logger.warning("Invalid API key", extra={"path": str(request.url.path)})
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"},
                    headers={"X-Request-ID": request_id},
                )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_var.reset(token)

# ── Health Endpoint (no auth) ────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health() -> Dict[str, str]:
    return {"status": "ok"}

# ── Credentials Functions ────────────────────────────────────────────────────

def fetch_credentials_from_service() -> Optional[Dict[str, Dict[str, str]]]:
    """
    Fetch credentials from the external credentials service.

    Returns:
        Dict mapping IP addresses to credentials, or None if service unavailable.
    """
    try:
        logger.info("Fetching credentials from service", extra={"url": CREDENTIALS_SERVICE_URL})
        response = requests.get(
            CREDENTIALS_SERVICE_URL,
            timeout=CREDENTIALS_SERVICE_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success") or "credentials" not in data:
            logger.warning("Invalid response structure from credentials service")
            return None

        credentials_dict: Dict[str, Dict[str, str]] = {}
        for cred in data["credentials"]:
            ip = cred.get("ip")
            if ip:
                credentials_dict[ip] = {
                    "username": cred.get("username", ""),
                    "password": cred.get("password", "")
                }

        logger.info("Fetched credentials from service", extra={"count": len(credentials_dict)})
        return credentials_dict

    except requests.exceptions.ConnectionError:
        logger.warning("Credentials service not reachable", extra={"url": CREDENTIALS_SERVICE_URL})
        return None
    except requests.exceptions.Timeout:
        logger.warning("Credentials service request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("Credentials service request failed", extra={"error": str(e)})
        return None
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Failed to parse credentials service response", extra={"error": str(e)})
        return None


def load_credentials_from_file() -> Dict[str, Dict[str, str]]:
    """Load credentials from the local config.json file."""
    config_path = "config.json"
    try:
        if not os.path.exists(config_path):
            logger.warning("Config file not found", extra={"path": config_path})
            return {}
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error loading credentials from file", extra={"error": str(e)})
        return {}


def save_credentials_to_file(credentials: Dict[str, Dict[str, str]]) -> None:
    """
    Write credentials to config.json.

    Writes directly to the file to ensure compatibility with Docker bind mounts,
    where rename-based atomic writes can silently fail to update the host file.

    Raises RuntimeError if the file cannot be written.
    """
    config_path = "config.json"
    try:
        with open(config_path, "w") as f:
            json.dump(credentials, f, indent=2)
        logger.info("Saved credentials to file", extra={"chassis_count": len(credentials)})
    except Exception as e:
        logger.error("Failed to write credentials file", extra={"error": str(e)})
        raise RuntimeError(f"Could not write to {config_path}: {e}")


def load_credentials(force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Load chassis credentials with fallback logic:
      1. Try to fetch from credentials service (cached for ttl seconds).
      2. Fall back to config.json if service is unavailable.

    Thread-safe via _cache_lock.
    """
    current_time = time.time()

    with _cache_lock:
        if not force_refresh and _credentials_cache["data"] is not None:
            if current_time - _credentials_cache["timestamp"] < _credentials_cache["ttl"]:
                logger.debug("Using cached credentials")
                return _credentials_cache["data"]

        credentials = fetch_credentials_from_service()

        if credentials is not None:
            _credentials_cache["data"] = credentials
            _credentials_cache["timestamp"] = current_time
            _credentials_cache["last_source"] = "service"
            return credentials

        logger.info("Falling back to config.json for credentials")
        file_credentials = load_credentials_from_file()
        _credentials_cache["data"] = file_credentials
        _credentials_cache["timestamp"] = current_time - (_credentials_cache["ttl"] / 2)
        _credentials_cache["last_source"] = "file"
        return file_credentials


# Initial credential load at startup
load_credentials()

# ── Pydantic Models ──────────────────────────────────────────────────────────

class ChassisCredentials(BaseModel):
    ip: str

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v!r}")
        return v


class ChassisCredentialInput(BaseModel):
    ip: str
    username: str
    password: str

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v!r}")
        return v


class ChassisCredentialRemove(BaseModel):
    ip: str

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v!r}")
        return v


class PortOperationCredentials(BaseModel):
    ip: str
    card_number: int
    port_number: int

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v!r}")
        return v


# ── Auth Helper ──────────────────────────────────────────────────────────────

def get_chassis_auth(ip: str) -> Dict[str, str]:
    """Return username/password for a chassis IP or raise 404."""
    chassis_creds = load_credentials()
    if ip not in chassis_creds:
        raise HTTPException(
            status_code=404,
            detail=f"No credentials configured for chassis {ip}. "
                   f"Add it to config.json or the credentials service."
        )
    return {
        "username": chassis_creds[ip]["username"],
        "password": chassis_creds[ip]["password"],
    }


# ── Chassis Endpoints ────────────────────────────────────────────────────────

@app.post("/chassis/summary", operation_id="get_chassis_summary")
def get_chassis_summary(credentials: ChassisCredentials) -> Dict[str, Any]:
    """
    Get hardware and software summary for a single chassis.

    Use this tool first when a user asks about a specific chassis. For per-card details
    use get_chassis_cards. For live CPU/memory use get_chassis_performance.
    For all chassis at once use get_all_chassis_summary.

    Example input: {"ip": "10.36.237.131"}

    Returns fields: chassisIp, chassisSerial#, controllerSerial#, chassisType,
    physicalCards# (count of installed cards), chassisStatus (Ready | Not Reachable),
    IxOS (version string), IxNetwork Protocols (version), mem_bytes, mem_bytes_total,
    cpu_pert_usage (percent), os (Linux | Windows), lastUpdatedAt_UTC.

    Windows chassis will have mem_bytes=NA and cpu_pert_usage=NA (no perf counters).
    Unreachable chassis return chassisStatus=Not Reachable with all other fields as NA.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        chassis_info = ixOSRestCaller.get_chassis_information(session)
        chassis_info["chassisIp"] = credentials.ip
        return chassis_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chassis summary failed", extra={"chassis": credentials.ip, "error": str(e)})
        return {
            "chassisIp": credentials.ip,
            "chassisSerial#": "NA",
            "controllerSerial#": "NA",
            "chassisType": "NA",
            "physicalCards#": "NA",
            "chassisStatus": "Not Reachable",
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
            "mem_bytes": "NA",
            "mem_bytes_total": "NA",
            "cpu_pert_usage": "NA",
            "os": "NA",
            "IxOS": "NA",
            "IxNetwork Protocols": "NA",
            "IxOS REST": "NA",
        }


@app.get("/chassis/all/summary", operation_id="get_all_chassis_summary")
async def get_all_chassis_summary() -> List[Dict[str, Any]]:
    """
    Get chassis hardware summary for ALL configured chassis in parallel.

    Use this tool when a user asks for a full lab inventory, overall health snapshot,
    or "show me all chassis". Runs concurrent requests so response time equals the
    slowest single chassis, not the sum.

    No input required.

    Returns: list of chassis summary objects — same fields as get_chassis_summary.
    Unreachable chassis appear with chassisStatus=Not Reachable rather than being omitted.
    """
    chassis_creds = load_credentials()
    chassis_ips = list(chassis_creds.keys())

    loop = asyncio.get_event_loop()

    def _fetch_one(ip: str) -> Dict[str, Any]:
        try:
            creds = chassis_creds[ip]
            session = IxRestSession(ip, creds["username"], creds["password"], verbose=False)
            info = ixOSRestCaller.get_chassis_information(session)
            info["chassisIp"] = ip
            return info
        except Exception as e:
            logger.warning("Could not reach chassis during bulk summary", extra={"chassis": ip, "error": str(e)})
            return {
                "chassisIp": ip,
                "chassisStatus": "Not Reachable",
                "chassisSerial#": "NA",
                "chassisType": "NA",
                "physicalCards#": "NA",
                "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
                "mem_bytes": "NA",
                "mem_bytes_total": "NA",
                "cpu_pert_usage": "NA",
                "os": "NA",
                "IxOS": "NA",
                "IxNetwork Protocols": "NA",
                "IxOS REST": "NA",
            }

    tasks = [loop.run_in_executor(None, _fetch_one, ip) for ip in chassis_ips]
    results = await asyncio.gather(*tasks)
    return list(results)


@app.post("/chassis/cards", operation_id="get_chassis_cards")
def get_chassis_cards(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get details for every card installed in the chassis.

    Use after get_chassis_summary when you need per-slot information. Use get_chassis_ports
    when you need port-level detail rather than card-level.

    Example input: {"ip": "10.36.237.131"}

    Returns list of card objects sorted by cardNumber. Fields per card:
    chassisIp, cardNumber (slot), serialNumber, cardType (e.g. NOVUS100GE8Q),
    cardState (Up | Down | Empty), numberOfPorts, lastUpdatedAt_UTC.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_chassis_cards_information(session, credentials.ip, "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Card info failed", extra={"chassis": credentials.ip, "error": str(e)})
        return [{
            "chassisIp": credentials.ip,
            "chassisType": "NA",
            "cardNumber": "NA",
            "serialNumber": "NA",
            "cardType": "NA",
            "cardState": "NA",
            "numberOfPorts": "NA",
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
        }]


@app.post("/chassis/ports", operation_id="get_chassis_ports")
def get_chassis_ports(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get status and ownership details for all ports in the chassis.

    Use to check which ports are free, who owns busy ports, link state, and transceiver info.
    Use get_chassis_cards for slot-level (not port-level) data.
    Use get_lldp_peer_data to see what device is physically connected to each port.

    Example input: {"ip": "10.36.237.131"}

    Returns list of port objects. Fields per port: cardNumber, portNumber,
    fullyQualifiedPortName (e.g. "1/1/1" or "4.1" on newer platforms), owner ("Free" if unowned), linkState,
    speed, phyMode, transceiverModel, transceiverManufacturer, lldpPeerData (dict or null).
    Aggregate stats appended to each port: totalPorts, ownedPorts, freePorts.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        logger.info("Getting chassis ports", extra={"chassis": credentials.ip})
        return ixOSRestCaller.get_chassis_ports_information(session, credentials.ip, "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Port info failed", extra={"chassis": credentials.ip, "error": str(e)})
        return [{
            "owner": "NA",
            "transceiverModel": "NA",
            "transceiverManufacturer": "NA",
            "portNumber": "NA",
            "linkState": "NA",
            "cardNumber": "NA",
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
            "totalPorts": "NA",
            "ownedPorts": "NA",
            "freePorts": "NA",
            "chassisIp": credentials.ip,
            "typeOfChassis": "NA",
        }]


@app.post("/chassis/licensing", operation_id="get_chassis_licensing")
def get_chassis_licensing(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get license activation details for a chassis.

    Use to verify license validity, check expiry dates, and retrieve activation codes.
    Note: this endpoint may take 10-20 seconds on some chassis due to license server polling.

    Example input: {"ip": "10.36.237.131"}

    Returns list of license objects. Fields per license: chassisIp, hostId,
    partNumber, activationCode, quantity, description, maintenanceDate,
    expiryDate (ISO date string or "NA"), isExpired (bool), lastUpdatedAt_UTC.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_license_activation(session, credentials.ip, "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("License info failed", extra={"chassis": credentials.ip, "error": str(e)})
        return [{
            "chassisIp": credentials.ip,
            "typeOfChassis": "NA",
            "hostId": "NA",
            "partNumber": "NA",
            "activationCode": "NA",
            "quantity": "NA",
            "description": "NA",
            "maintenanceDate": "NA",
            "expiryDate": "NA",
            "isExpired": "NA",
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
        }]


@app.post("/chassis/sensors", operation_id="get_chassis_sensors")
def get_chassis_sensors(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get sensor readings (temperature, voltage, fan speed) from the chassis.

    Use for thermal health monitoring or to diagnose hardware alerts.
    Use get_chassis_performance for CPU/memory instead of sensors.

    Example input: {"ip": "10.36.237.131"}

    Returns list of sensor objects. Fields: type (Temperature | Voltage | Fan),
    name (sensor label), value (numeric reading), unit (Celsius | Volts | RPM),
    chassisIp, lastUpdatedAt_UTC.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_sensor_information(session, credentials.ip, "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Sensor info failed", extra={"chassis": credentials.ip, "error": str(e)})
        return [{
            "type": "NA",
            "unit": "NA",
            "name": "NA",
            "value": "NA",
            "chassisIp": credentials.ip,
            "typeOfChassis": "NA",
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
        }]


@app.post("/chassis/performance", operation_id="get_chassis_performance")
def get_chassis_performance(credentials: ChassisCredentials) -> Dict[str, Any]:
    """
    Get live CPU and memory utilization for a chassis.

    Use for real-time resource monitoring. Use get_chassis_summary for a snapshot
    that includes performance alongside hardware details.
    Not available on Windows chassis (returns 0 values).

    Example input: {"ip": "10.36.237.131"}

    Returns: chassisIp, mem_utilization (percent, float), cpu_utilization (percent, float),
    lastUpdatedAt_UTC.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_perf_metrics(session, credentials.ip)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Performance metrics failed", extra={"chassis": credentials.ip, "error": str(e)})
        return {
            "chassisIp": credentials.ip,
            "mem_utilization": 0,
            "cpu_utilization": 0,
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
        }


@app.get("/chassis/list", operation_id="get_chassis_list")
def get_chassis_list() -> List[str]:
    """
    List all chassis IP addresses configured in the system.

    Use this tool first to discover available chassis before calling any
    chassis-specific tools. Returns only the IPs — use get_chassis_summary
    or get_all_chassis_summary for hardware details.

    No input required.

    Returns: list of IP address strings, e.g. ["10.36.237.131", "10.36.236.121"].
    Empty list means no chassis are configured.
    """
    try:
        chassis_creds = load_credentials()
        return list(chassis_creds.keys())
    except Exception as e:
        logger.error("Chassis list failed", extra={"error": str(e)})
        return []


@app.post("/chassis/lldp", operation_id="get_lldp_peer_data")
def get_lldp_peer_data(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get LLDP neighbor data for all ports that have a discovered peer.

    Use to map physical topology — which DUT port connects to which chassis port.
    Only ports with an active LLDP peer are returned; ports with no peer are omitted.
    An empty list means no LLDP peers are discovered (not an error).

    Example input: {"ip": "10.36.237.131"}

    Returns list of LLDP peer objects. Fields per entry: portName (chassis port identifier),
    portId (peer port ID), portDescription, systemMac, systemIp, systemName (peer hostname),
    lastUpdatedAt_UTC.
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        logger.info("Getting LLDP peer data", extra={"chassis": credentials.ip})
        chassis_ports = ixOSRestCaller.get_chassis_ports_information(session, credentials.ip, "")
        lldp_peer_data = []
        for port in chassis_ports:
            port_name = port.get("fullyQualifiedPortName", port.get("portNumber"))
            if port.get("lldpPeerData"):
                port["lldpPeerData"].update({"portName": port_name})
                lldp_peer_data.append(port["lldpPeerData"])
        return lldp_peer_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLDP peer data failed", extra={"chassis": credentials.ip, "error": str(e)})
        return [{
            "portName": "NA",
            "portId": "NA",
            "portDescription": "NA",
            "systemMac": "NA",
            "systemIp": "NA",
            "systemName": "NA",
            "chassisIp": credentials.ip,
            "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
        }]


# ── Port Operation Helper ────────────────────────────────────────────────────

def get_port_id(session: IxRestSession, card_number: int, port_number: int) -> int:
    """
    Resolve card/port numbers to the chassis internal port ID.

    Raises HTTPException(404) if the port does not exist on this chassis.
    """
    ports = session.get_ports(params={"cardNumber": card_number, "portNumber": port_number}).data
    if not ports:
        raise HTTPException(
            status_code=404,
            detail=f"Port {card_number}/{port_number} not found on chassis"
        )
    return ports[0]["id"]


# ── Port Operation Endpoints ─────────────────────────────────────────────────

@app.post("/chassis/take_port_ownership", operation_id="take_port_ownership")
def take_port_ownership(credentials: PortOperationCredentials) -> Dict[str, Any]:
    """
    Take ownership of a port to reserve it for test use.

    Linux chassis only — not supported on Windows chassis.
    Use get_chassis_ports first to verify the port is Free before taking ownership.
    Use release_port_ownership when done to free the port for others.

    Example input: {"ip": "10.36.237.131", "card_number": 1, "port_number": 1}

    Returns on success: success=true, chassisIp, cardNumber, portNumber, portId, message.
    Raises 404 if port card/port number not found.
    Raises 502 if chassis rejects the operation (e.g. port already owned by another user).
    """
    auth = get_chassis_auth(credentials.ip)
    session = IxRestSession(credentials.ip, auth["username"], auth["password"], verbose=False)
    port_id = get_port_id(session, credentials.card_number, credentials.port_number)

    try:
        logger.info(
            "Taking port ownership",
            extra={"chassis": credentials.ip, "card": credentials.card_number, "port": credentials.port_number}
        )
        session.take_ownership(port_id)
    except Exception as e:
        logger.error("Chassis rejected take_ownership", extra={"chassis": credentials.ip, "error": str(e)})
        raise HTTPException(status_code=502, detail=f"Chassis operation failed: {str(e)}")

    return {
        "success": True,
        "chassisIp": credentials.ip,
        "cardNumber": credentials.card_number,
        "portNumber": credentials.port_number,
        "portId": port_id,
        "message": "Port ownership taken successfully",
        "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
    }


@app.post("/chassis/release_port_ownership", operation_id="release_port_ownership")
def release_port_ownership(credentials: PortOperationCredentials) -> Dict[str, Any]:
    """
    Release ownership of a port, making it available for others.

    Linux chassis only — not supported on Windows chassis.
    Use after completing a test to free the port. Use get_chassis_ports to confirm
    the port shows owner=Free after release.

    Example input: {"ip": "10.36.237.131", "card_number": 1, "port_number": 1}

    Returns on success: success=true, chassisIp, cardNumber, portNumber, portId, message.
    Raises 404 if port not found. Raises 502 if chassis rejects the operation.
    """
    auth = get_chassis_auth(credentials.ip)
    session = IxRestSession(credentials.ip, auth["username"], auth["password"], verbose=False)
    port_id = get_port_id(session, credentials.card_number, credentials.port_number)

    try:
        logger.info(
            "Releasing port ownership",
            extra={"chassis": credentials.ip, "card": credentials.card_number, "port": credentials.port_number}
        )
        session.release_ownership(port_id)
    except Exception as e:
        logger.error("Chassis rejected release_ownership", extra={"chassis": credentials.ip, "error": str(e)})
        raise HTTPException(status_code=502, detail=f"Chassis operation failed: {str(e)}")

    return {
        "success": True,
        "chassisIp": credentials.ip,
        "cardNumber": credentials.card_number,
        "portNumber": credentials.port_number,
        "portId": port_id,
        "message": "Port ownership released successfully",
        "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
    }


@app.post("/chassis/reboot_port", operation_id="reboot_port")
def reboot_port(credentials: PortOperationCredentials) -> Dict[str, Any]:
    """
    Reboot a port (power-cycle the port ASIC) for troubleshooting link issues.

    Linux chassis only — not supported on Windows chassis.
    Use when a port is stuck in a bad state and link cannot be restored by other means.
    Port will be briefly unavailable during reboot (typically 10-30 seconds).

    Example input: {"ip": "10.36.237.131", "card_number": 1, "port_number": 1}

    Returns on success: success=true, chassisIp, cardNumber, portNumber, portId, message.
    Raises 404 if port not found. Raises 502 if chassis rejects the operation.
    """
    auth = get_chassis_auth(credentials.ip)
    session = IxRestSession(credentials.ip, auth["username"], auth["password"], verbose=False)
    port_id = get_port_id(session, credentials.card_number, credentials.port_number)

    try:
        logger.info(
            "Rebooting port",
            extra={"chassis": credentials.ip, "card": credentials.card_number, "port": credentials.port_number}
        )
        session.reboot_port(port_id)
    except Exception as e:
        logger.error("Chassis rejected reboot_port", extra={"chassis": credentials.ip, "error": str(e)})
        raise HTTPException(status_code=502, detail=f"Chassis operation failed: {str(e)}")

    return {
        "success": True,
        "chassisIp": credentials.ip,
        "cardNumber": credentials.card_number,
        "portNumber": credentials.port_number,
        "portId": port_id,
        "message": "Port rebooted successfully",
        "lastUpdatedAt_UTC": datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
    }


# ── Credentials Management Endpoints ────────────────────────────────────────

@app.post("/credentials/refresh", operation_id="refresh_credentials")
def refresh_credentials() -> Dict[str, Any]:
    """
    Force reload chassis credentials, bypassing the 60-second cache.

    Use when you have just added or changed chassis credentials in config.json
    or the credentials service and want the changes reflected immediately.
    Automatically tries the credentials service first, falls back to config.json.

    No input required.

    Returns: success, source ("credentials_service" | "config.json"),
    chassis_count, chassis_ips list, message.
    """
    credentials = load_credentials(force_refresh=True)

    with _cache_lock:
        source = _credentials_cache.get("last_source")

    if source == "service":
        return {
            "success": True,
            "source": "credentials_service",
            "service_url": CREDENTIALS_SERVICE_URL,
            "chassis_count": len(credentials),
            "chassis_ips": list(credentials.keys()),
            "message": "Credentials refreshed from credentials service",
        }

    return {
        "success": True,
        "source": "config.json",
        "service_url": CREDENTIALS_SERVICE_URL,
        "service_available": False,
        "chassis_count": len(credentials),
        "chassis_ips": list(credentials.keys()),
        "message": "Credentials loaded from config.json (credentials service unavailable)",
    }


@app.get("/credentials/status", operation_id="get_credentials_status")
def get_credentials_status() -> Dict[str, Any]:
    """
    Return current credential source and cache state without making any network calls.

    Use to diagnose why a chassis IP is missing from the list, or to verify
    which credential source is active. Does not trigger a credentials refresh.

    No input required.

    Returns: credentials_service_url, credentials_service_available (bool, from last load),
    cache_ttl_seconds (60), cache_age_seconds, cache_valid (bool),
    chassis_count, chassis_ips list.
    """
    current_time = time.time()

    with _cache_lock:
        timestamp = _credentials_cache["timestamp"]
        ttl = _credentials_cache["ttl"]
        last_source = _credentials_cache.get("last_source")
        credentials = _credentials_cache.get("data") or {}

    cache_age = current_time - timestamp if timestamp > 0 else None
    cache_valid = cache_age is not None and cache_age < ttl

    return {
        "credentials_service_url": CREDENTIALS_SERVICE_URL,
        "credentials_service_available": last_source == "service",
        "credentials_service_timeout": CREDENTIALS_SERVICE_TIMEOUT,
        "cache_ttl_seconds": ttl,
        "cache_age_seconds": round(cache_age, 2) if cache_age is not None else None,
        "cache_valid": cache_valid,
        "chassis_count": len(credentials),
        "chassis_ips": list(credentials.keys()),
    }


# ── Chassis Credential CRUD ──────────────────────────────────────────────────

@app.post("/chassis/credentials", operation_id="add_chassis_credentials")
def add_chassis_credentials(entry: ChassisCredentialInput) -> Dict[str, Any]:
    """
    Add or update credentials for a chassis so it can be queried by other tools.

    Takes effect immediately — no server restart or credentials refresh needed.
    Persists to config.json so the chassis survives container restarts.

    If a credentials service is also configured, entries added here are stored
    in config.json (the fallback). They remain active in memory immediately but
    may be overridden at next cache refresh if the credentials service does not
    include this IP. Use get_credentials_status to check the active source.

    Example input: {"ip": "10.36.237.131", "username": "admin", "password": "admin"}

    Returns: success, message, chassis_ips (full updated list).
    """
    with _cache_lock:
        current = dict(_credentials_cache.get("data") or load_credentials_from_file())
        is_update = entry.ip in current
        current[entry.ip] = {"username": entry.username, "password": entry.password}

        try:
            save_credentials_to_file(current)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        _credentials_cache["data"] = current
        _credentials_cache["timestamp"] = time.time()
        _credentials_cache["last_source"] = "file"

    action = "updated" if is_update else "added"
    logger.info(f"Chassis credentials {action}", extra={"chassis": entry.ip})
    return {
        "success": True,
        "action": action,
        "chassis_ip": entry.ip,
        "chassis_ips": list(current.keys()),
        "chassis_count": len(current),
        "message": f"Chassis {entry.ip} {action} successfully. Ready to use immediately.",
    }


@app.post("/chassis/credentials/remove", operation_id="remove_chassis_credentials")
def remove_chassis_credentials(entry: ChassisCredentialRemove) -> Dict[str, Any]:
    """
    Remove a chassis from the system so it no longer appears in queries.

    Takes effect immediately and persists to config.json.

    Example input: {"ip": "10.36.237.131"}

    Returns: success, message, chassis_ips (remaining list).
    Raises 404 if the chassis IP is not in the current configuration.
    """
    with _cache_lock:
        current = dict(_credentials_cache.get("data") or load_credentials_from_file())

        if entry.ip not in current:
            raise HTTPException(
                status_code=404,
                detail=f"Chassis {entry.ip} not found in configuration."
            )

        del current[entry.ip]

        try:
            save_credentials_to_file(current)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        _credentials_cache["data"] = current
        _credentials_cache["timestamp"] = time.time()
        _credentials_cache["last_source"] = "file"

    logger.info("Chassis credentials removed", extra={"chassis": entry.ip})
    return {
        "success": True,
        "chassis_ip": entry.ip,
        "chassis_ips": list(current.keys()),
        "chassis_count": len(current),
        "message": f"Chassis {entry.ip} removed successfully.",
    }


# ── MCP Mount ────────────────────────────────────────────────────────────────

mcp = FastApiMCP(
    app,
    name="IxNetwork Inventory MCP",
    description="MCP tools for managing IxNetwork chassis inventory and metrics"
)
mcp.mount()

# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("MCP_SERVER_PORT", "8888"))
    print(f"Starting IxNetwork Inventory MCP Server on port {port}")
    print(f"MCP endpoint:    http://localhost:{port}/mcp")
    print(f"API docs:        http://localhost:{port}/docs")
    print(f"Health check:    http://localhost:{port}/health")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
