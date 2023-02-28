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
    
    
    chassis_filter_dict.update({ "IP": d["managementIp"],
                                 "chassisSN": d.get("serialNumber", no_serial_string),
                                 "controllerSN": d.get("controllerSerialNumber", "NA"),
                                 "type": d["type"].replace(" ", "_"),
                                 "# PhysicalCards": str(d.get("numberOfPhysicalCards", "NA")),
                                })
    
    # List of Application on Ix CHhssis
    list_of_ixos_protocols = d["ixosApplications"]
    
    for item in list_of_ixos_protocols:
        if item["name"] != "IxOS REST":
           temp_dict.update({item["name"]: item["version"]})

    if d["type"] == "Ixia Virtual Test Appliance":
        no_serial_string = "IxiaVM"
        
    chassis_filter_dict.update(temp_dict)
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
        
def get_license_host_id(session):
    return session.get_license_server_host_id()

    
def get_portstats(session):
    license_info = session.get_portstats().json()
    print("\n******************* Port Statistics ***********************\n")
    df = pd.DataFrame(license_info)
    print(df)

def start_chassis_rest_data_fetch(chassis, username, password, operation=None):
    final_table_dict = {}
    session = IxRestSession(chassis, username= username, password=password, verbose=False)
    cin = get_chassis_information(session)
    type_chassis = cin["type"]
    if operation == "chassisSummary":
        final_table_dict.update(cin)
    elif operation == "cardDetails":
        final_table_dict.update({"cardDetails": get_chassis_cards_information(session), "ip": f"{chassis} ===> {type_chassis}"})
    elif operation == "licenseDetails":
        host_id = get_license_host_id(session)
        final_table_dict.update({"licenseDetails": get_license_activation(session), "ip": f"{chassis} ===> {type_chassis} ::: hostId - {host_id}"})
    return final_table_dict