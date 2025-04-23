"""
IxNetwork Chassis Information Collector

This module provides functions to collect information from Ixia Chassis using REST APIs.
It interfaces with the IxNetwork REST API to gather chassis details, card information,
port statistics, licensing information, and performance metrics.

Reference: 
    https://<chassis_ip>/chassis/swagger/index.html#/

Functions:
    - get_chassis_information: Get chassis hardware and system details
    - get_chassis_cards_information: Get information about cards installed
    - get_chassis_ports_information: Get port status and configuration
    - get_license_activation: Get licensing information
    - get_sensor_information: Get chassis sensor readings
    - get_perf_metrics: Get performance metrics

Author: Keysight Technologies
"""

import json
import math
from datetime import datetime, timezone
import logging
import time

logger = logging.getLogger(__name__)

def convert_size(size_bytes):
    """
    Convert bytes to human readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Human readable size string (e.g., "1.5 GB")
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def get_perf_metrics(session, chassisIp):
    """
    Get chassis performance metrics including CPU and memory utilization.
    
    Args:
        session (IxRestSession): Active REST session to the chassis
        chassisIp (str): IP address of the chassis
        
    Returns:
        dict: Performance metrics including:
            - chassisIp: IP address of chassis
            - mem_utilization: Memory utilization percentage
            - cpu_utilization: CPU utilization percentage
            - lastUpdatedAt_UTC: Timestamp of the data
    """
    logger.info(f"Getting performance metrics for chassis {chassisIp}")
    chassis_perf_dict = {}
    try:
        perf = session.get_perfcounters().data[0]
        mem_bytes = int(perf.get("memoryInUseBytes", "0"))
        mem_bytes_total = int(perf.get("memoryTotalBytes", "0"))
        cpu_pert_usage = perf.get("cpuUsagePercent", "0")
        mem_util = (mem_bytes/mem_bytes_total)*100 if mem_bytes_total else 0
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        mem_util = 0
        cpu_pert_usage = 0
    
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    return {
        "chassisIp": chassisIp,
        "mem_utilization": mem_util, 
        "cpu_utilization": cpu_pert_usage,
        "lastUpdatedAt_UTC": last_update_at
    }
    
def get_chassis_information(session):
    """
    Get comprehensive chassis information including hardware details and system metrics.
    
    Args:
        session (IxRestSession): Active REST session to the chassis
        
    Returns:
        dict: Chassis information including:
            - chassisIp: Management IP address
            - chassisSerial#: Chassis serial number
            - controllerSerial#: Controller serial number
            - chassisType: Type of chassis
            - physicalCards#: Number of physical cards
            - chassisStatus: Current operational status
            - mem_bytes: Current memory usage
            - mem_bytes_total: Total system memory
            - cpu_pert_usage: CPU utilization percentage
            - os: Operating system type
            - Various IxOS application versions
    """
    logger.info("Getting chassis information")
    chassis_filter_dict = {}
    no_serial_string = ""
    mem_bytes = "NA"
    mem_bytes_total = "NA"
    cpu_pert_usage = "NA"
    os = "Linux"
    
    try:
        chassisInfo = session.get_chassis()
        chassis_data = json.loads(json.dumps(chassisInfo.data[0]))
        
        try:
            perf = session.get_perfcounters().data[0]
            mem_bytes = convert_size(perf["memoryInUseBytes"])
            mem_bytes_total = convert_size(perf["memoryTotalBytes"])
            cpu_pert_usage = perf["cpuUsagePercent"]
        except Exception:
            logger.warning("Performance metrics not available, chassis may be Windows-based")
            os = "Windows"
            
        if chassis_data["type"] == "Ixia_Virtual_Test_Appliance":
            no_serial_string = "IxiaVM"
        
        chassis_filter_dict = {
            "chassisIp": chassis_data.get("managementIp"),
            "chassisSerial#": chassis_data.get("serialNumber", no_serial_string),
            "controllerSerial#": chassis_data.get("controllerSerialNumber", "NA"),
            "chassisType": chassis_data["type"].replace(" ", "_"),
            "physicalCards#": str(chassis_data.get("numberOfPhysicalCards", "NA")),
            "chassisStatus": chassis_data.get('state'),
            "lastUpdatedAt_UTC": datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S"),
            "mem_bytes": mem_bytes, 
            "mem_bytes_total": mem_bytes_total, 
            "cpu_pert_usage": cpu_pert_usage,
            "os": os
        }
        
        # Add IxOS application versions
        for item in chassis_data["ixosApplications"]:
            if item["name"] not in ["IxOS REST", "LicenseServerPlus"]:
                chassis_filter_dict[item["name"]] = item["version"]
                
    except Exception as e:
        logger.error(f"Error getting chassis information: {str(e)}")
        raise
        
    return chassis_filter_dict
    
def get_chassis_cards_information(session, ip, type_of_chassis):
    """
    Get detailed information about all cards installed in the chassis.
    
    Args:
        session (IxRestSession): Active REST session to the chassis
        ip (str): IP address of the chassis
        type_of_chassis (str): Type of the chassis
        
    Returns:
        list: List of dictionaries containing card information:
            - chassisIp: IP address of chassis
            - chassisType: Type of chassis
            - cardNumber: Card slot number
            - serialNumber: Card serial number
            - cardType: Type of card
            - cardState: Current state of the card
            - numberOfPorts: Number of ports on the card
            - lastUpdatedAt_UTC: Timestamp of the data
    """
    logger.info(f"Getting card information for chassis {ip}")
    try:
        card_list = session.get_cards().data
        final_card_details_list = []
        last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
        
        # Sort cards by card number
        sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
        
        for sc in sorted_cards:
            final_card_details_list.append({
                "chassisIp": ip, 
                "chassisType": type_of_chassis,
                "cardNumber": sc.get("cardNumber"), 
                "serialNumber": sc.get("serialNumber"),
                "cardType": sc.get("type"),
                "cardState": sc.get("state"), 
                "numberOfPorts": sc.get("numberOfPorts", "No data"),
                "lastUpdatedAt_UTC": last_update_at
            })
        return final_card_details_list
    except Exception as e:
        logger.error(f"Error getting card information: {str(e)}")
        raise
    
def get_chassis_ports_information(session, chassisIp, chassisType):
    """
    Get detailed information about all ports in the chassis.
    
    Args:
        session (IxRestSession): Active REST session to the chassis
        chassisIp (str): IP address of the chassis
        chassisType (str): Type of the chassis
        
    Returns:
        list: List of dictionaries containing port information:
            - owner: Current owner of the port
            - transceiverModel: Model of the transceiver
            - transceiverManufacturer: Manufacturer of the transceiver
            - cardNumber: Card number
            - portNumber: Port number
            - phyMode: Physical mode
            - linkState: Current link state
            - speed: Port speed
            - type: Port type
            - totalPorts: Total number of ports
            - ownedPorts: Number of owned ports
            - freePorts: Number of free ports
    """
    logger.info(f"Getting port information for chassis {chassisIp}")
    try:
        port_list = session.get_ports().data
        last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
        
        # Define relevant keys to keep
        keys_to_keep = ['owner', 'transceiverModel', 'transceiverManufacturer', 
                       'cardNumber', 'portNumber', 'phyMode', 'linkState', 'speed', 'type']
        
        # Process port information
        if port_list:
            keys_to_remove = [x for x in port_list[0].keys() if x not in keys_to_keep]
            total_ports = len(port_list)
            
            # Clean up port data
            for port in port_list:
                if not port.get("owner"):
                    port["owner"] = "Free"
                for k in keys_to_remove:
                    port.pop(k)
                    
            # Calculate port statistics
            used_ports = len([p for p in port_list if p.get("owner") != "Free"])
            free_ports = total_ports - used_ports
            
            # Add additional information to each port
            for port in port_list:
                port.update({
                    "lastUpdatedAt_UTC": last_update_at,
                    "totalPorts": total_ports,
                    "ownedPorts": used_ports,
                    "freePorts": free_ports,
                    "chassisIp": chassisIp,
                    "typeOfChassis": chassisType
                })
                
            return port_list
        return []
    except Exception as e:
        logger.error(f"Error getting port information: {str(e)}")
        raise

def get_license_activation(session, chassis_ip, chassis_type):
    """Get license activation details from chassis
    Args:
        session: IxRestSession object
        chassis_ip: IP address of chassis
        chassis_type: Type of chassis
    Returns:
        List of dictionaries containing license information
    """
    try:
        # Initial license activation request
        license_info = session.get_license_activation().json()
        
        # Poll until we get complete license information
        max_retries = 10
        retry_count = 0
        retry_delay = 2  # seconds
        
        while retry_count < max_retries:
            # Check if we have complete license information
            if license_info and isinstance(license_info, list) and all(isinstance(item, dict) and 'activationCode' in item for item in license_info):
                break
                
            # Wait before retrying
            time.sleep(retry_delay)
            
            # Retry getting license information
            license_info = session.get_license_activation().json()
            retry_count += 1
            
            logger.debug(f"License info polling attempt {retry_count}: {license_info}")
        
        if not license_info or retry_count >= max_retries:
            logger.warning(f"Could not get complete license information after {max_retries} attempts")
            return [{
                'chassisIp': chassis_ip,
                'typeOfChassis': chassis_type,
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

        # Process the license information
        processed_licenses = []
        for license in license_info:
            processed_license = {
                'chassisIp': chassis_ip,
                'typeOfChassis': chassis_type,
                'hostId': license.get('hostId', 'NA'),
                'partNumber': license.get('partNumber', 'NA'),
                'activationCode': license.get('activationCode', 'NA'),
                'quantity': license.get('quantity', 'NA'),
                'description': license.get('description', 'NA'),
                'maintenanceDate': license.get('maintenanceDate', 'NA'),
                'expiryDate': license.get('expiryDate', 'NA'),
                'isExpired': license.get('isExpired', 'NA'),
                'lastUpdatedAt_UTC': datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
            }
            processed_licenses.append(processed_license)
            
        return processed_licenses
        
    except Exception as e:
        logger.error(f"Error getting license activation for chassis {chassis_ip}: {str(e)}")
        return [{
            'chassisIp': chassis_ip,
            'typeOfChassis': chassis_type,
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

def get_sensor_information(session, chassis, type_chassis):
    """
    Get sensor readings from the chassis.
    
    Args:
        session (IxRestSession): Active REST session to the chassis
        chassis (str): IP address of the chassis
        type_chassis (str): Type of the chassis
        
    Returns:
        list: List of dictionaries containing sensor information:
            - type: Sensor type
            - unit: Measurement unit
            - name: Sensor name
            - value: Current sensor value
            - chassisIp: IP address of chassis
            - typeOfChassis: Type of chassis
    """
    logger.info(f"Getting sensor information for chassis {chassis}")
    try:
        sensor_list = session.get_sensors().json()
        keys_to_remove = ["criticalValue", "maxValue", 'parentId', 'id',
                         'adapterName', 'minValue', 'sensorSetName', 'cpuName']
        
        last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
        
        for record in sensor_list:
            for item in keys_to_remove:
                record.pop(item, "NA")
            record.update({
                "chassisIp": chassis,
                "typeOfChassis": type_chassis,
                "lastUpdatedAt_UTC": last_update_at
            })
            
        return sensor_list
    except Exception as e:
        logger.error(f"Error getting sensor information: {str(e)}")
        raise