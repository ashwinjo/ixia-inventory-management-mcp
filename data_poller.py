from sqlite3_utilities import *
import IxOSRestCallerModifier as ixOSRestCaller
from RestApi.IxOSRestInterface import IxRestSession
import click
import time
import json



def get_chassis_summary_data():
    """This is a call to RestAPI to get chassis summary data
    """
    list_of_chassis = []
    serv_list = read_username_password_from_database()
    if serv_list:
        chassis_list = json.loads(serv_list)
        for chassis in chassis_list:
            try:
                session = IxRestSession(
                    chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_chassis_information(session)
                out["chassisIp"] = chassis["ip"]
                list_of_chassis.append(out)
            except Exception:
                list_of_chassis.append({ "chassisIp": chassis["ip"],
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
                    "IxOS REST": "NA"})
                    

        write_data_to_database(table_name="chassis_summary_details",
                            records=list_of_chassis, ip_tags_dict={})
    else:
        print("No Chassis List")


def get_chassis_card_data():
    """This is a call to RestAPI to get chassis card summary data
    """
    list_of_cards = []
    serv_list = read_username_password_from_database()
    if serv_list:
        chassis_list = json.loads(serv_list)
        for chassis in chassis_list:
            try:
                session = IxRestSession(
                    chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_chassis_cards_information(
                    session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
                list_of_cards.append(out)
            except Exception:
                out = [{'chassisIp': chassis["ip"], 
                       'chassisType': 'NA', 
                       'cardNumber': 'NA', 
                       'serialNumber': 'NA', 
                       'cardType': 'NA', 
                       'cardState': 'NA', 
                       'numberOfPorts': 'NA', 
                       'lastUpdatedAt_UTC': 'NA'}]
                list_of_cards.append(out)
        
        write_data_to_database(table_name="chassis_card_details",
                            records=list_of_cards, ip_tags_dict={})


def get_chassis_port_data():
    """This is a call to RestAPI to get chassis card port summary data
    """
    port_list_details = []
    serv_list = read_username_password_from_database()
    if serv_list:
        chassis_list = json.loads(serv_list)
        if chassis_list:
            for chassis in chassis_list:
                try:
                    session = IxRestSession(
                        chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                    out = ixOSRestCaller.get_chassis_ports_information(
                        session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
                    port_list_details.append(out)
                except Exception:
                    a = [{
                        'owner': 'NA',
                        'transceiverModel': 'NA',
                        'transceiverManufacturer': 'NA',
                        'portNumber': 'NA',
                        'linkState': 'NA',
                        'cardNumber': 'NA',
                        'lastUpdatedAt_UTC': 'NA',
                        'totalPorts': 'NA',
                        'ownedPorts': 'NA',
                        'freePorts': 'NA',
                        'chassisIp': chassis["ip"],
                        'typeOfChassis': 'NA'
                    }]
                    port_list_details.append(a)
            write_data_to_database(
                table_name="chassis_port_details", records=port_list_details)


def get_chassis_licensing_data():
    """This is a call to RestAPI to get chassis licensing data
    """
    list_of_licenses = []
    serv_list = read_username_password_from_database()
    if serv_list:
        chassis_list = json.loads(serv_list)
        for chassis in chassis_list:
            try:
                session = IxRestSession(
                    chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_license_activation(
                    session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
                list_of_licenses.append(out)
            except Exception:
                a = [{
                'chassisIp': chassis["ip"],
                'typeOfChassis': 'NA',
                'hostId': 'NA',
                'partNumber': 'NA',
                'activationCode': 'NA',
                'quantity': 'NA',
                'description': 'NA',
                'maintenanceDate': 'NA',
                'expiryDate': 'NA',
                'isExpired': 'NA',
                'lastUpdatedAt_UTC': 'NA'
                }]
                list_of_licenses.append(a)
        write_data_to_database(
            table_name="license_details_records", records=list_of_licenses)

def get_sensor_information():
    """This is a call to RestAPI to get chassis sensors summary data
    """
    sensor_list_details = []
    serv_list = read_username_password_from_database()
    if serv_list:
        chassis_list = json.loads(serv_list)
        for chassis in chassis_list:
            try:
                session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_sensor_information(session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
                sensor_list_details.append(out)
            except Exception:
                a =   [{
                        'type': 'NA',
                        'unit': 'NA',
                        'name': 'NA',
                        'value': 'NA',
                        'chassisIp': chassis["ip"],
                        'typeOfChassis': 'NA',
                        'lastUpdatedAt_UTC': 'NA'
                    }]
                sensor_list_details.append(a)
        write_data_to_database(
            table_name="chassis_sensor_details", records=sensor_list_details)

def get_perf_metrics():
    """This is a call to RestAPI to get chassis performance metrics data
    """
    serv_list = read_username_password_from_database()
    perf_list_details = []
    if serv_list:
        chassis_list = json.loads(serv_list)
        for chassis in chassis_list:
            try:
                session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_perf_metrics(session, chassis["ip"])
                perf_list_details.append(out)
            except Exception:
                a = {'chassisIp': chassis["ip"], 
                     'mem_utilization': 0, 
                     'cpu_utilization': 0, 
                     'lastUpdatedAt_UTC': '03/15/2023, 03:31:47'}
                perf_list_details.append(a)
        write_data_to_database(
            table_name="chassis_utilization_details", records=perf_list_details)
        
def delete_half_metric_records_weekly():
    """This method will do periodic cleanup of inventord DB performance metrics data
    """
    pass


def controller(category_of_poll=None):
    categoryToFuntionMap[category_of_poll]()


categoryToFuntionMap = {"chassis": get_chassis_summary_data,
                        "cards": get_chassis_card_data,
                        "ports": get_chassis_port_data,
                        "licensing": get_chassis_licensing_data,
                        "sensors": get_sensor_information,
                        "perf": get_perf_metrics}



@click.command()
@click.option('--category', default= "", help='What chassis aspect to poll. chassis, cards, ports, licensing')
@click.option('--interval', default= "", help='Interval between Polls')
def start_poller(category, interval): 
    """Since not all the parameters are modified with same interval, this way, we can specify exactly what we want to monitor at what interval
  Args:
        categoryOfPoll (_type_): _description_
        frequencyInSeconds (_type_): _description_
    """
    while True:
        poll_interval = read_poll_setting_from_database()
        if poll_interval:
            interval = poll_interval[category]
        categoryToFuntionMap[category]()
        time.sleep(int(interval))

if __name__ == '__main__':
    start_poller()