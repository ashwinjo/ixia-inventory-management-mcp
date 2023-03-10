"""
Description
-----------
This tool belongs to Keysight Technologies

This file implements code for collecting information from Ixia Chassis usinf Rest API's
Reference: https://<chassis_ip>/chassis/swagger/index.html#/
User has to pass a list or a string IP addresses. 
It collects the below info from the chassis:
    - chassis-model
    - ixos-version
    - license details (if any)
    - ports
    - cpu_utilization
    - card-models
"""

import json
import math
from  RestApi.IxOSRestInterface import IxRestSession
from datetime import datetime, timezone



def get_sensors_information(session):
    out = session.get_sensors()

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

    
def get_chassis_information(session):
    """ Fetch chassis information from RestPy
    We also get the perf counters in the same call
    """
    temp_dict = {}
    chassis_filter_dict = {}
    no_serial_string = ""
    mem_bytes = "NA"
    mem_bytes_total = "NA"
    cpu_pert_usage =  "NA"
    os = "Linux"
    
    chassisInfo = session.get_chassis()
    
    try:
        # Exception Handling for Windows Chassis
        perf = session.get_perfcounters().data[0]
        mem_bytes = convert_size(perf["memoryInUseBytes"])
        mem_bytes_total = convert_size(perf["memoryTotalBytes"])
        cpu_pert_usage = perf["cpuUsagePercent"]
    except Exception:
        os = "Windows"
        
    
    chassis_data = json.loads(json.dumps(chassisInfo.data[0]))
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    
    if chassis_data["type"] == "Ixia_Virtual_Test_Appliance":
        no_serial_string = "IxiaVM"
    
    chassis_filter_dict.update({ "chassisIp": chassis_data.get("managementIp"),
                                 "chassisSerial#": chassis_data.get("serialNumber", no_serial_string),
                                 "controllerSerial#": chassis_data.get("controllerSerialNumber", "NA"),
                                 "chassisType": chassis_data["type"].replace(" ", "_"),
                                 "physicalCards#": str(chassis_data.get("numberOfPhysicalCards", "NA")),
                                 "chassisStatus": chassis_data.get('state'),
                                 "lastUpdatedAt_UTC": last_update_at,
                                 "mem_bytes": mem_bytes, 
                                 "mem_bytes_total": mem_bytes_total, 
                                 "cpu_pert_usage": cpu_pert_usage,
                                 "os": os
                                })
    
    # List of Application on Ix CHhssis
    list_of_ixos_protocols = chassis_data["ixosApplications"]    
    for item in list_of_ixos_protocols:
        if item["name"] != "IxOS REST" or item["name"] != "LicenseServerPlus":
           temp_dict.update({item["name"]: item["version"]})
        
    chassis_filter_dict.update(temp_dict)
    return chassis_filter_dict
    
def get_chassis_cards_information(session, ip, type_of_chassis):
    """_summary_
    """
    card_list= session.get_cards().data
    final_card_details_list= []
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    # Cards on Chassis
    sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
    
    
    for sc  in sorted_cards:
        final_card_details_list.append({"chassisIp": ip, 
                                        "chassisType": type_of_chassis,
                                        "cardNumber":sc.get("cardNumber"), 
                                        "serialNumber": sc.get("serialNumber"),
                                        "cardType": sc.get("type"), 
                                        "numberOfPorts":sc.get("numberOfPorts", "No data"),
                                        "lastUpdatedAt_UTC": last_update_at
                                        })
    return final_card_details_list
    
def get_chassis_ports_information(session, chassisIp, chassisType):
    """_summary_
    """
    
    port_data_list = []
    used_port_details = []
    total_ports = 0
    used_ports = 0
    
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    port_list = session.get_ports().data
    
    keys_to_keep = ['owner', 'transceiverModel', 'transceiverManufacturer', 'cardNumber', 'portNumber', 'phyMode']

    if port_list:
        a = list(port_list[0].keys())
    else:
        a = []
    keys_to_remove = [x for x in a if x not in keys_to_keep]
    
    # Removing the extra keys from port details json response
    for port_data in port_list:
        for k in keys_to_remove:
            port_data.pop(k)
    
    for port in port_list:
        port_data_list.append(port)
    
    # Lets get used ports, free ports and total ports
    if port_data_list:
        used_port_details = [item for item in port_data_list if item.get("owner")]
        total_ports = len(port_list)
        used_ports = len(used_port_details)
        
    
    
    for port_data_list_item in port_data_list:
        port_data_list_item.update({
                                "lastUpdatedAt_UTC": last_update_at,
                                "totalPorts": total_ports,
                                "ownedPorts": used_ports, 
                                "freePorts": (total_ports-used_ports),
                                "chassisIp": chassisIp,
                                "typeOfChassis": chassisType })
    return port_data_list

        
def get_license_activation(session, ip, type_chassis):
    host_id = session.get_license_server_host_id()
    license_info = session.get_license_activation().json()
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    license_info_list= []
    for item in license_info:
        license_info_list.append({
                "chassisIp": ip,
                "typeOfChassis": type_chassis,
                "hostId": host_id,
                "partNumber": item["partNumber"],
                "activationCode": item["activationCode"], 
                "quantity": item["quantity"], 
                "description": item["description"].replace(",","_"),
                "maintenanceDate": item["maintenanceDate"], 
                "expiryDate": item["expiryDate"],
                "isExpired": str(item.get("isExpired", "NA")),
                "lastUpdatedAt_UTC": last_update_at})
    return license_info_list


def get_sensor_information(session, chassis, type_chassis):
    td = session.get_sensors().json()
    keys_to_remove = ["criticalValue", "maxValue", 'parentId', 'id','adapterName','minValue','sensorSetName', 'cpuName']
    for record in td:
        for item in keys_to_remove:
            record.pop(item)
        record.update({"chassisIp":chassis, "chassisType": type_chassis})
        
    return td