from sqlite3_utilities_new import write_data_to_database, getChassistypeFromIp, read_username_password_from_database, read_poll_setting_from_database
import IxOSRestCallerModifier as ixOSRestCaller
from RestApi.IxOSRestInterface import IxRestSession
import click
import time
import json
from datetime import datetime, timezone


def get_chassis_summary_data():
    """This is a call to RestAPI to get chassis summary data

    Returns:
        _type_: _description_
    """
    list_of_chassis = []
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        print(CHASSIS_LIST)
        for chassis in CHASSIS_LIST:
            session = IxRestSession(
                chassis["ip"], chassis["username"], chassis["password"], verbose=False)
            out = ixOSRestCaller.get_chassis_information(session)
            list_of_chassis.append(out)

        write_data_to_database(table_name="chassis_summary_details",
                            records=list_of_chassis, ip_tags_dict={})
    else:
        print("No Chassis List")


def get_chassis_card_data():
    """This is a call to RestAPI to get chassis summary data

    Returns:
        _type_: _description_
    """
    list_of_cards = []
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        print(CHASSIS_LIST)
        for chassis in CHASSIS_LIST:
            session = IxRestSession(
                chassis["ip"], chassis["username"], chassis["password"], verbose=False)
            out = ixOSRestCaller.get_chassis_cards_information(
                session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
            list_of_cards.append(out)

        write_data_to_database(table_name="chassis_card_details",
                            records=list_of_cards, ip_tags_dict={})


def get_chassis_port_data():
    """_summary_
    """
    port_list_details = []
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        if CHASSIS_LIST:
            for chassis in CHASSIS_LIST:
                session = IxRestSession(
                    chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_chassis_ports_information(
                    session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
                port_list_details.append(out)
            write_data_to_database(
                table_name="chassis_port_details", records=port_list_details)


def get_chassis_licensing_data():
    list_of_licenses = []
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        print(CHASSIS_LIST)
        for chassis in CHASSIS_LIST:
            session = IxRestSession(
                chassis["ip"], chassis["username"], chassis["password"], verbose=False)
            out = ixOSRestCaller.get_license_activation(
                session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
            list_of_licenses.append(out)
        write_data_to_database(
            table_name="license_details_records", records=list_of_licenses)

def get_sensor_information():
    headers = ["chassisIP", "chassisType", "sensorType", "sensorName", "sensorValue"]
    sensor_list_details = []
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        print(CHASSIS_LIST)
        for chassis in CHASSIS_LIST:
            session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
            out = ixOSRestCaller.get_sensor_information(session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
            sensor_list_details.append(out)
        write_data_to_database(
            table_name="chassis_sensor_details", records=sensor_list_details)

def get_perf_metrics():
    serv_list = read_username_password_from_database()
    perf_list_details = []
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        print(CHASSIS_LIST)
        for chassis in CHASSIS_LIST:
            session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
            out = ixOSRestCaller.get_perf_metrics(session, chassis["ip"])
            perf_list_details.append(out)
        print(perf_list_details)
        write_data_to_database(
            table_name="chassis_utilization_details", records=perf_list_details)



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
        print(interval)
        time.sleep(int(interval))

if __name__ == '__main__':
    start_poller()