from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from RestApi.IxOSRestInterface import IxRestSession
import IxOSRestCallerModifier as ixOSRestCaller

from datetime import datetime
import logging

#Configure logging 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IxNetwork Inventory API",
    description="API for managing IxNetwork chassis inventory and metrics",
    version="1.0.0"
)

class ChassisCredentials(BaseModel):
    """
    Pydantic model for chassis credentials
    """
    ip: str
    username: str
    password: str

@app.post("/chassis/summary", operation_id="get_chassis_summary")
def get_chassis_summary(credentials: ChassisCredentials) -> Dict[str, Any]:
    """
    Get chassis summary information including hardware details and system metrics.
    
    Args:
        credentials (ChassisCredentials): Chassis connection credentials in request body
            - ip: IP address of the chassis
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip, 
            credentials.username, 
            credentials.password, 
            verbose=False
        )
        chassis_info = ixOSRestCaller.get_chassis_information(session)
        chassis_info["chassisIp"] = credentials.ip
        return chassis_info
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
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip,
            credentials.username,
            credentials.password,
            verbose=False
        )
        return ixOSRestCaller.get_chassis_cards_information(
            session, 
            credentials.ip,
            ""
        )
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
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip,
            credentials.username,
            credentials.password,
            verbose=False
        )
        logger.info(f"Getting chassis ports for {credentials}")
        return ixOSRestCaller.get_chassis_ports_information(
            session,
            credentials.ip,
            ""
        )
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
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip,
            credentials.username,
            credentials.password,
            verbose=False
        )
        return ixOSRestCaller.get_license_activation(
            session,
            credentials.ip,
            ""  # Chassis type will be determined by the caller
        )
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
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip,
            credentials.username,
            credentials.password,
            verbose=False
        )
        return ixOSRestCaller.get_sensor_information(
            session,
            credentials.ip,
            ""  # Chassis type will be determined by the caller
        )
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
            - username: Username for authentication
            - password: Password for authentication
    """
    try:
        session = IxRestSession(
            credentials.ip,
            credentials.username,
            credentials.password,
            verbose=False
        )
        return ixOSRestCaller.get_perf_metrics(session, credentials.ip)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return {
            'chassisIp': credentials.ip,
            'mem_utilization': 0,
            'cpu_utilization': 0,
            'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
        }

# Initialize MCP after all routes are defined
mcp = FastApiMCP(
    app,
    name="IxNetwork Inventory MCP",
    description="MCP tools for managing IxNetwork chassis inventory and metrics"
)

# Mount MCP server
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server at http://localhost:8888/mcp")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")