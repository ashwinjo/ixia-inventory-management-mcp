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
import tabulate
import pandas as pd
from  RestApi.IxOSRestInterface import IxRestSession


def get_owned_ports(port_data_list):
    op = [item for item in port_data_list if item.get("owner")]
    print("******************* Ports ownership details ***********************")
    print (pd.DataFrame(op))
    return len(op), op

    
def get_chassis_information(session):
    """ Fetch chassis information from RestPy
    """
    temp_dict = {}
    chassis_filter_dict = {}
    chassisInfo = session.get_chassis()
    perf = session.get_perfcounters().data[0]
    
    d = json.loads(json.dumps(chassisInfo.data[0]))
    chassis_state = chassisInfo.data[0]['state'].upper()
    list_of_ixos_protocols = d["ixosApplications"]
    for item in list_of_ixos_protocols:
        temp_dict.update({item["name"]: item["version"]})

    chassis_filter_dict.update(temp_dict)
    chassis_filter_dict.update({"chassisSerielNumber": d["serialNumber"],
                                "mgmtIp": d["managementIp"],
                                "controllerSerialNumber": d.get("controllerSerialNumber", "NA"),
                                "type": d["type"],
                                "numberOfPhysicalCards": str(d.get("numberOfPhysicalCards", "NA")),
                                "state": chassis_state,
                                "memoryInUseBytes": perf["memoryInUseBytes"], 
                                "memoryTotalBytes": perf["memoryTotalBytes"], 
                                "diskIOBytesPerSecond": perf["diskIOBytesPerSecond"],  
                                "cpuUsagePercent": perf["cpuUsagePercent"]
                                })
    return chassis_filter_dict
    
def get_chassis_cards_information(session):
    """_summary_
    """
    card_list= session.get_cards().data
    
    # Cards on Chassis
    sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
    return sorted_cards

    
def get_chassis_ports_information(session):
    """_summary_
    """
    # Ports on Chassis
    port_data_list = []
    port_list = session.get_ports().data
    df = pd.DataFrame(port_list)
    print("******************* Ports details ***********************")
    print(df)
    
    for port in port_list:
        port_data_list.append(port)
    total_ports = len(port_list)
    
    
        
    # Metric 1: Port Owned vs Ports Free
    op_count, op_result = get_owned_ports(port_data_list)
    free_ports = total_ports - op_count
    percent_ports_owned = (op_count/total_ports) * 100
    percent_ports_free = (free_ports/total_ports) * 100
    
    print("\n******************* Percentage ports having owners ***********************\n")
    print("% ports owned total",  percent_ports_owned)
    print("% ports free total",  percent_ports_free)


    # Metric 2: Users on Chassis + #ports used
    list_of_users = [user["owner"].split("/")[-1] for user in op_result]
    print("\n******************* Users on Chassis ***********************\n")
    for x in set(list_of_users):
        print ("{0}:--{1}".format(x, list_of_users.count(x)))
        
def get_license_activation(session):
    license_info = session.get_license_activation().json()
    l= []
    for item in license_info:
        l.append({"activationCode": item["activationCode"], 
                "quantity": item["quantity"], 
                "description": item["description"], 
                "expiryDate": item["expiryDate"]})
    return l
    
def get_portstats(session):
    license_info = session.get_portstats().json()
    print("\n******************* Port Statistics ***********************\n")
    df = pd.DataFrame(license_info)
    print(df)

def start_chassis_rest_data_fetch(chassis, username, password):
    session = IxRestSession(chassis, username= username, password=password, verbose=False)
    complete_response = {} 
    complete_response["chassis_information"] = get_chassis_information(session)
    complete_response["cards_information"] = get_chassis_cards_information(session)
    #complete_response["license_information"] = get_license_activation(session)
    return complete_response
