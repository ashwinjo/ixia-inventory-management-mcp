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
import pandas as pd
from  RestApi.IxOSRestInterface import IxRestSession

    
def get_chassis_information(session):
    """ Fetch chassis information from RestPy
    """
    temp_dict = {}
    no_serial_string = ""
    chassis_filter_dict = {}
    chassisInfo = session.get_chassis()
    try:
        perf = session.get_perfcounters().data[0]
    except Exception:
        pass
    
    
    d = json.loads(json.dumps(chassisInfo.data[0]))
    
    chassis_state = chassisInfo.data[0]['state'].upper()
    
    chassis_filter_dict.update({ "IP": d.get("managementIp"),
                                 "chassisSN": d.get("serialNumber", no_serial_string),
                                 "controllerSN": d.get("controllerSerialNumber", "NA"),
                                 "type": d["type"].replace(" ", "_"),
                                 "# PhysicalCards": str(d.get("numberOfPhysicalCards", "NA")),
                                 "status": chassis_state
                                })
    
    # List of Application on Ix CHhssis
    list_of_ixos_protocols = d["ixosApplications"]
    
    for item in list_of_ixos_protocols:
        if item["name"] != "IxOS REST" or item["name"] != "LicenseServerPlus":
           temp_dict.update({item["name"]: item["version"]})

    if d["type"] == "Ixia_Virtual_Test_Appliance":
        no_serial_string = "IxiaVM"
        
    chassis_filter_dict.update(temp_dict)
    return chassis_filter_dict
    
def get_chassis_cards_information(session, ip, type_of_chassis):
    """_summary_
    """
    card_list= session.get_cards().data
    final_card_details_list= []
    # Cards on Chassis
    sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
    for sc  in sorted_cards:
        final_card_details_list.append({"ip": ip, "type_of_chassis": type_of_chassis,
                                        "cardNumber":sc.get("cardNumber"), 
                                        "serialNumber": sc.get("serialNumber"),
                                        "type": sc.get("type"), 
                                        "numberOfPorts":sc.get("numberOfPorts", "No data")})
    return final_card_details_list
    
def get_chassis_ports_information(session):
    """_summary_
    """
    port_summary = {}
    m = []

    port_data_list = []
    port_list = session.get_ports().data
    keys_to_keep = ['owner', 'transceiverModel', 'transceiverManufacturer', 'cardNumber', 'portNumber', 'phyMode']

    """{
	'owner': 'BreakingPoint/admin/8',
	'transceiverModel': 'FCBN425QB1C03',
	'captureState': False,
	'ownedState': '',
	'simulatedCableState': 'NotSimulated',
	'type': '100GBASE SR4 - BreakingPoint',
	'portMemory': 16384,
	'pcpuStatus': 'PCPUREADY',
	'fullyQualifiedPortName': 'N/A',
	'transceiverManufacturer': 'FINISAR',
	'portNumber': 1,
	'speed': 100000,
	'parentId': 1118,
	'linkState': 'UP',
	'managementIp': '10.0.3.1',
	'transmitState': False,
	'transceiverSerialNumber': 'DTS01WE',
	'id': 1119,
	'phyMode': 'COPPER',
	'cardNumber': 3
}
    """
    if port_list:
        a = list(port_list[0].keys())
    else:
        a = []
    keys_to_remove = [x for x in a if x not in keys_to_keep]
    
    for port_data in port_list:
        for k in keys_to_remove:
            port_data.pop(k)
    
    for port in port_list:
        port_data_list.append(port)
    
    if port_data_list:
        used_port_details = [item for item in port_data_list if item.get("owner")]
        total_ports = len(port_list)
        used_ports = len(used_port_details)
    else:
        used_port_details = []
        total_ports = []
        used_ports = []
    
    return {"used_port_details": used_port_details, "total_ports": total_ports, "used_ports": used_ports}



def get_port_usage_stats():
    # port_summary["% ports owned"] = percent_ports_owned
    # port_summary["% ports free"] = percent_ports_free
    

    
    # # Metric 2: Users on Chassis + #ports used
    # list_of_users = [user["owner"] for user in op_result]
    # for x in set(list_of_users):
    #     m.append("{0}:--{1}".format(x, list_of_users.count(x)))
    # port_summary["users_on_chassis"] =  m
    # return port_summary
    pass
        
def get_license_activation(session, ip, type_chassis, host_id):
    license_info = session.get_license_activation().json()
    data= []
    for item in license_info:
        data.append({
                "chassisIp": ip,
                "typeOfChassis": type_chassis,
                "hostId": host_id,
                "partNumber": item["partNumber"],
                "activationCode": item["activationCode"], 
                "quantity": item["quantity"], 
                "description": item["description"],
                "maintenanceDate": item["maintenanceDate"], 
                "expiryDate": item["expiryDate"],
                "isExpired": str(item["isExpired"])})
    return data
        
def get_license_host_id(session):
    return session.get_license_server_host_id()

def start_chassis_rest_data_fetch(chassis, username, password, operation=None):
    final_table_dict = {}
    session = IxRestSession(chassis, username= username, password=password, verbose=False)
    cin = get_chassis_information(session)
    type_chassis = cin["type"]
    if operation == "chassisSummary":
        final_table_dict.update(cin)
    elif operation == "cardDetails":
        final_table_dict = get_chassis_cards_information(session, chassis, type_chassis)
    elif operation == "licenseDetails":
        host_id = get_license_host_id(session)
        final_table_dict = get_license_activation(session, chassis, type_chassis, host_id)
    elif operation == "portDetails":
        out = get_chassis_ports_information(session)
        final_table_dict.update({"portDetails": out.get("used_port_details"), 
                                 "used_ports":  out.get("used_ports"),
                                 "total_ports" :  out.get("total_ports"),
                                 "ctype": f"{type_chassis}", 
                                 "ip": f"{chassis}"})
    return final_table_dict