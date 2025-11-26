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

#Configure logging 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IxNetwork Inventory API",
    description="API for managing IxNetwork chassis inventory and metrics",
    version="1.0.0"
)

# Load chassis credentials from config file
def load_credentials():
    config_path = "config.json"
    try:
        # Check if file exists
        if not os.path.exists(config_path):
            logger.warning(f"Config file {config_path} not found. Using empty credentials dictionary.")
            return {}
            
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        return {}

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


