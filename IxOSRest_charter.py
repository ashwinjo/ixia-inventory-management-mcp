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
import json2table
from  RestApi.IxOSRestInterface import IxRestSession


def get_owned_ports(port_data_list):
    op = [item for item in port_data_list if item.get("owner")]
    return len(op), op

    
def get_chassis_information(session):
    """ Fetch chassis information from RestPy
    """
    temp_dict = {}
    no_serial_string = ""
    chassis_filter_dict = {}
    chassisInfo = session.get_chassis()
    perf = session.get_perfcounters().data[0]
    
    d = json.loads(json.dumps(chassisInfo.data[0]))
    chassis_state = chassisInfo.data[0]['state'].upper()
    list_of_ixos_protocols = d["ixosApplications"]
    for item in list_of_ixos_protocols:
        temp_dict.update({item["name"]: item["version"]})

    if d["type"] == "Ixia Virtual Test Appliance":
        no_serial_string = "IxiaVM"
        
    chassis_filter_dict.update(temp_dict)
    chassis_filter_dict.update({"chassisSerielNumber": d.get("serialNumber", no_serial_string),
                                "mgmtIp": d["managementIp"],
                                "controllerSerialNumber": d.get("controllerSerialNumber", "NA"),
                                "type": d["type"].replace(" ", "_"),
                                "numberOfPhysicalCards": str(d.get("numberOfPhysicalCards", "NA")),
                                "memoryInUseBytes": perf["memoryInUseBytes"], 
                                "memoryTotalBytes": perf["memoryTotalBytes"], 
                                "diskIOBytesPerSecond": perf["diskIOBytesPerSecond"],  
                                "cpuUsagePercent": perf["cpuUsagePercent"],
                                # "id": d["id"]
                                })
    return chassis_filter_dict
    
def get_chassis_cards_information(session):
    """_summary_
    """
    card_list= session.get_cards().data
    final_card_details_list= []
    # Cards on Chassis
    sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
    for sc  in sorted_cards:
        final_card_details_list.append({"cardNumber":sc.get("cardNumber"), "type": sc.get("type"), "numberOfPorts":sc.get("numberOfPorts")})
    return final_card_details_list
    
def get_chassis_ports_information(session):
    """_summary_
    """
    port_summary = {}
    m = []
    # Ports on Chassis
    port_data_list = []
    port_list = session.get_ports().data
    for port in port_list:
        port_data_list.append(port)
    total_ports = len(port_list)
        
    # Metric 1: Port Owned vs Ports Free
    op_count, op_result = get_owned_ports(port_data_list)
    free_ports = total_ports - op_count
    if total_ports:
        percent_ports_owned = (op_count/total_ports) * 100
        percent_ports_free = (free_ports/total_ports) * 100
    else: 
        percent_ports_owned = 0
        percent_ports_free = 0
        
    
    print("% ports owned total",  percent_ports_owned)
    print("% ports free total",  percent_ports_free)
    
    #port_summary["ownership_details"] = op_result
    port_summary["% ports owned"] = percent_ports_owned
    port_summary["% ports free"] = percent_ports_free
    

    
    # Metric 2: Users on Chassis + #ports used
    list_of_users = [user["owner"] for user in op_result]
    for x in set(list_of_users):
        m.append("{0}:--{1}".format(x, list_of_users.count(x)))
    port_summary["users_on_chassis"] =  m
    return port_summary
        
def get_license_activation(session):
    license_info = session.get_license_activation().json()
    data= []
    for item in license_info:
        data.append({"activationCode": item["activationCode"], 
                "quantity": item["quantity"], 
                "description": item["description"], 
                "expiryDate": item["expiryDate"]})
        
    return data
        
    
    
def get_portstats(session):
    license_info = session.get_portstats().json()
    print("\n******************* Port Statistics ***********************\n")
    df = pd.DataFrame(license_info)
    print(df)
    
def collect_chassis_logs(session):
    resultURL = session.collect_chassis_logs()
    return resultURL

def start_chassis_rest_data_fetch(chassis, username, password):
    final_table_dict = {}
    session = IxRestSession(chassis, username= username, password=password, verbose=False)
    final_table_dict = get_chassis_information(session)
    final_table_dict.update({"cardDetails": get_chassis_cards_information(session)})
    final_table_dict.update({"licenseDetails": get_license_activation(session)})
    
    
    infoFromJson = json.loads(json.dumps(final_table_dict))
    build_direction = "LEFT_TO_RIGHT"
    return json2table.convert(infoFromJson, build_direction=build_direction)
    