from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from RestApi.IxOSRestInterface import IxRestSession
import IxOSRestCallerModifier as ixOSRestCaller

from datetime import datetime
import logging
import json
import os
import requests
import time

#Configure logging 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IxNetwork Inventory API",
    description="API for managing IxNetwork chassis inventory and metrics",
    version="1.0.0"
)

# Credentials service configuration
CREDENTIALS_SERVICE_URL = os.environ.get(
    "CREDENTIALS_SERVICE_URL", 
    "http://localhost:3001/api/config/credentials"
)
CREDENTIALS_SERVICE_TIMEOUT = int(os.environ.get("CREDENTIALS_SERVICE_TIMEOUT", "5"))

# Credentials cache
_credentials_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 60  # Cache TTL in seconds
}

def fetch_credentials_from_service() -> Optional[Dict[str, Dict[str, str]]]:
    """
    Fetch credentials from the external credentials service.
    
    Returns:
        Dict mapping IP addresses to credentials, or None if service unavailable
    """
    try:
        logger.info(f"Fetching credentials from service: {CREDENTIALS_SERVICE_URL}")
        response = requests.get(
            CREDENTIALS_SERVICE_URL, 
            timeout=CREDENTIALS_SERVICE_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response structure
        if not data.get("success") or "credentials" not in data:
            logger.warning("Invalid response structure from credentials service")
            return None
        
        # Transform the service response to our expected format
        # From: {"credentials": [{"ip": "x.x.x.x", "username": "...", "password": "..."}]}
        # To: {"x.x.x.x": {"username": "...", "password": "..."}}
        credentials_dict = {}
        for cred in data["credentials"]:
            ip = cred.get("ip")
            if ip:
                credentials_dict[ip] = {
                    "username": cred.get("username", ""),
                    "password": cred.get("password", "")
                }
        
        logger.info(f"Successfully fetched {len(credentials_dict)} credentials from service")
        return credentials_dict
        
    except requests.exceptions.ConnectionError:
        logger.warning(f"Credentials service not available at {CREDENTIALS_SERVICE_URL}")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout connecting to credentials service")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching from credentials service: {str(e)}")
        return None
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Error parsing credentials service response: {str(e)}")
        return None

def load_credentials_from_file() -> Dict[str, Dict[str, str]]:
    """
    Load credentials from the local config.json file.
    
    Returns:
        Dict mapping IP addresses to credentials
    """
    config_path = "config.json"
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Config file {config_path} not found. Using empty credentials dictionary.")
            return {}
            
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials from file: {str(e)}")
        return {}

def load_credentials(force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Load chassis credentials with fallback logic:
    1. Try to fetch from credentials service
    2. Fall back to config.json if service is unavailable
    
    Uses caching to avoid hitting the service on every request.
    
    Args:
        force_refresh: If True, bypass the cache and fetch fresh credentials
        
    Returns:
        Dict mapping IP addresses to credentials
    """
    global _credentials_cache
    
    current_time = time.time()
    
    # Check if cache is valid
    if not force_refresh and _credentials_cache["data"] is not None:
        if current_time - _credentials_cache["timestamp"] < _credentials_cache["ttl"]:
            logger.debug("Using cached credentials")
            return _credentials_cache["data"]
    
    # Try to fetch from service first
    credentials = fetch_credentials_from_service()
    
    if credentials is not None:
        # Update cache with service credentials
        _credentials_cache["data"] = credentials
        _credentials_cache["timestamp"] = current_time
        return credentials
    
    # Fall back to file-based credentials
    logger.info("Falling back to config.json for credentials")
    file_credentials = load_credentials_from_file()
    
    # Cache the file credentials too (but with a shorter effective cache 
    # since we want to retry the service)
    _credentials_cache["data"] = file_credentials
    _credentials_cache["timestamp"] = current_time - (_credentials_cache["ttl"] / 2)  # Retry service sooner
    
    return file_credentials

# Initial load of credentials
CHASSIS_CREDENTIALS = load_credentials()

class ChassisCredentials(BaseModel):
    """
    Pydantic model for chassis credentials
    """
    ip: str

def get_chassis_auth(ip):
    """
    Get authentication details for a chassis from config file
    """
    chassis_creds = load_credentials()
    if ip not in chassis_creds:
        raise HTTPException(status_code=404, detail=f"Credentials for chassis {ip} not found in config")
    
    return {
        "username": chassis_creds[ip]["username"],
        "password": chassis_creds[ip]["password"]
    }

@app.post("/chassis/summary", operation_id="get_chassis_summary")
def get_chassis_summary(credentials: ChassisCredentials) -> Dict[str, Any]:
    """
    Get chassis summary information including hardware details and system metrics.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
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
    except HTTPException as e:
        raise e
    except Exception as e:
        return {
            "chassisIp": credentials.ip,
            "chassisSerial#": "NA",
            "controllerSerial#": "NA",
            "chassisType": "NA",
            "physicalCards#": "NA",
            "chassisStatus": "Not Reachable",
            "lastUpdatedAt_UTC": "NA",
            "mem_bytes": "NA",
            "mem_bytes_total": "NA",
            "cpu_pert_usage": "NA",
            "os": "NA",
            "IxOS": "NA",
            "IxNetwork Protocols": "NA",
            "IxOS REST": "NA"
        }

@app.post("/chassis/cards", operation_id="get_chassis_cards")
def get_chassis_cards(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get information about all cards in the chassis.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_chassis_cards_information(
            session, 
            credentials.ip,
            ""
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting card information: {str(e)}")
        return [{
            'chassisIp': credentials.ip,
            'chassisType': 'NA',
            'cardNumber': 'NA',
            'serialNumber': 'NA',
            'cardType': 'NA',
            'cardState': 'NA',
            'numberOfPorts': 'NA',
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }]

@app.post("/chassis/ports", operation_id="get_chassis_ports")
def get_chassis_ports(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get information about all ports in the chassis.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        logger.info(f"Getting chassis ports for {credentials}")
        return ixOSRestCaller.get_chassis_ports_information(
            session,
            credentials.ip,
            ""
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting chassis ports: {str(e)}")
        return [{
            'owner': 'NA',
            'transceiverModel': 'NA',
            'transceiverManufacturer': 'NA',
            'portNumber': 'NA',
            'linkState': 'NA',
            'cardNumber': 'NA',
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
            'totalPorts': 'NA',
            'ownedPorts': 'NA',
            'freePorts': 'NA',
            'chassisIp': credentials.ip,
            'typeOfChassis': 'NA'
        }]

@app.post("/chassis/licensing", operation_id="get_chassis_licensing")
def get_chassis_licensing(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get chassis licensing information.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_license_activation(
            session,
            credentials.ip,
            ""  # Chassis type will be determined by the caller
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting licensing information: {str(e)}")
        return [{
            'chassisIp': credentials.ip,
            'typeOfChassis': 'NA',
            'hostId': 'NA',
            'partNumber': 'NA',
            'activationCode': 'NA',
            'quantity': 'NA',
            'description': 'NA',
            'maintenanceDate': 'NA',
            'expiryDate': 'NA',
            'isExpired': 'NA',
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }]

@app.post("/chassis/sensors", operation_id="get_chassis_sensors")
def get_chassis_sensors(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get chassis sensor information.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        return ixOSRestCaller.get_sensor_information(
            session,
            credentials.ip,
            ""  # Chassis type will be determined by the caller
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting sensor information: {str(e)}")
        return [{
            'type': 'NA',
            'unit': 'NA',
            'name': 'NA',
            'value': 'NA',
            'chassisIp': credentials.ip,
            'typeOfChassis': 'NA',
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }]

@app.post("/chassis/performance", operation_id="get_chassis_performance")
def get_chassis_performance(credentials: ChassisCredentials) -> Dict[str, Any]:
    """
    Get chassis performance metrics.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return {
            'chassisIp': credentials.ip,
            'mem_utilization': 0,
            'cpu_utilization': 0,
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }

@app.get("/chassis/list", operation_id="get_chassis_list")
def get_chassis_list() -> List[str]:
    """
    Get list of all chassis IPs available in the configuration.
    Returns:
        List[str]: List of IP addresses for all configured chassis
    """
    try:
        chassis_creds = load_credentials()
        return list(chassis_creds.keys())
    except Exception as e:
        logger.error(f"Error getting chassis list: {str(e)}")
        return []

@app.post("/chassis/lldp", operation_id="get_lldp_peer_data")
def get_lldp_peer_data(credentials: ChassisCredentials) -> List[Dict[str, Any]]:
    """
    Get LLDP peer data for each port on the chassis
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
        
    Returns:
        list: List of dictionaries containing LLDP peer data
    """
    try:
        auth = get_chassis_auth(credentials.ip)
        session = IxRestSession(
            credentials.ip,
            auth["username"],
            auth["password"],
            verbose=False
        )
        logger.info(f"Getting LLDP peer data for {credentials.ip}")
        chassis_ports = ixOSRestCaller.get_chassis_ports_information(
            session,
            credentials.ip,
            ""
        )
        lldp_peer_data = []
        for port in chassis_ports:
            port_name = port.get("fullyQualifiedPortName", port.get("portNumber"))
            if port.get("lldpPeerData"):
                port["lldpPeerData"].update({"portName": port_name})
                lldp_peer_data.append(port["lldpPeerData"])
        return lldp_peer_data
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting LLDP peer data: {str(e)}")
        return [{
            'portName': 'NA',
            'portId': 'NA',
            'portDescription': 'NA',
            'systemMac': 'NA',
            'systemIp': 'NA',
            'systemName': 'NA',
            'chassisIp': credentials.ip,
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }]

@app.post("/credentials/refresh", operation_id="refresh_credentials")
def refresh_credentials() -> Dict[str, Any]:
    """
    Force refresh credentials from the credentials service.
    Falls back to config.json if service is unavailable.
    
    Returns:
        Dict containing refresh status and source of credentials
    """
    global _credentials_cache
    
    # Clear cache to force refresh
    _credentials_cache["data"] = None
    _credentials_cache["timestamp"] = 0
    
    # Try service first
    service_credentials = fetch_credentials_from_service()
    
    if service_credentials is not None:
        _credentials_cache["data"] = service_credentials
        _credentials_cache["timestamp"] = time.time()
        return {
            "success": True,
            "source": "credentials_service",
            "service_url": CREDENTIALS_SERVICE_URL,
            "chassis_count": len(service_credentials),
            "chassis_ips": list(service_credentials.keys()),
            "message": "Credentials refreshed from credentials service"
        }
    
    # Fall back to file
    file_credentials = load_credentials_from_file()
    _credentials_cache["data"] = file_credentials
    _credentials_cache["timestamp"] = time.time() - (_credentials_cache["ttl"] / 2)
    
    return {
        "success": True,
        "source": "config.json",
        "service_url": CREDENTIALS_SERVICE_URL,
        "service_available": False,
        "chassis_count": len(file_credentials),
        "chassis_ips": list(file_credentials.keys()),
        "message": "Credentials loaded from config.json (credentials service unavailable)"
    }

@app.get("/credentials/status", operation_id="get_credentials_status")
def get_credentials_status() -> Dict[str, Any]:
    """
    Get the current status of credentials including source and cache information.
    
    Returns:
        Dict containing credentials status information
    """
    current_time = time.time()
    cache_age = current_time - _credentials_cache["timestamp"] if _credentials_cache["timestamp"] > 0 else None
    cache_valid = cache_age is not None and cache_age < _credentials_cache["ttl"]
    
    # Check if service is available
    service_available = fetch_credentials_from_service() is not None
    
    credentials = load_credentials()
    
    return {
        "credentials_service_url": CREDENTIALS_SERVICE_URL,
        "credentials_service_available": service_available,
        "credentials_service_timeout": CREDENTIALS_SERVICE_TIMEOUT,
        "cache_ttl_seconds": _credentials_cache["ttl"],
        "cache_age_seconds": round(cache_age, 2) if cache_age else None,
        "cache_valid": cache_valid,
        "chassis_count": len(credentials),
        "chassis_ips": list(credentials.keys())
    }

# Initialize MCP after all routes are defined
mcp = FastApiMCP(
    app,
    name="IxNetwork Inventory MCP",
    description="MCP tools for managing IxNetwork chassis inventory and metrics"
)

# Mount MCP server with streaming support at /mcp endpoint
# Using default mount path '/mcp' and default router (the main FastAPI app)
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IxNetwork Inventory MCP Server")
    print("📍 MCP endpoint: http://localhost:8888/mcp")
    print("📚 API documentation: http://localhost:8888/docs")
    print("🔄 Streamable HTTP MCP server is ready for Claude Desktop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")


