from sqlite3_utilities_new import write_data_to_database, getChassistypeFromIp
import  IxOSRestCallerModifier as ixOSRestCaller 
from RestApi.IxOSRestInterface import IxRestSession
from config import CHASSIS_LIST


def get_chassis_summary_data():
    """This is a call to RestAPI to get chassis summary data

    Returns:
        _type_: _description_
    """
    list_of_chassis = [] 
    
    for chassis in CHASSIS_LIST:
        session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
        out = ixOSRestCaller.get_chassis_information(session)
        list_of_chassis.append(out)
    
    write_data_to_database(table_name="chassis_summary_details", records=list_of_chassis, ip_tags_dict={})
    
def get_chassis_card_data():
    """This is a call to RestAPI to get chassis summary data

    Returns:
        _type_: _description_
    """
    list_of_cards = [] 
    
    for chassis in CHASSIS_LIST:
        session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
        out = ixOSRestCaller.get_chassis_cards_information(session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
        list_of_cards.append(out)
    
    write_data_to_database(table_name="chassis_card_details", records=list_of_cards, ip_tags_dict={})
    

def get_chassis_port_data():
    """_summary_
    """
    port_list_details = []
    for chassis in CHASSIS_LIST:
        session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
        out = ixOSRestCaller.get_chassis_ports_information(session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
        port_list_details.append(out)
    write_data_to_database(table_name="chassis_port_details", records=port_list_details)


def get_chassis_licensing_data():
    list_of_licenses = []
    for chassis in CHASSIS_LIST:
        session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"], verbose=False)
        out = ixOSRestCaller.get_license_activation(session, chassis["ip"], getChassistypeFromIp(chassis["ip"]))
        list_of_licenses.append(out)
    write_data_to_database(table_name="license_details_records", records=list_of_licenses)
    


def controller(type_of_poll=None, category_of_poll=None):
    if type_of_poll == "periodic":
        pass
    elif type_of_poll=="onDemand":
        categoryToFuntionMap[category_of_poll]()


categoryToFuntionMap = {"chassis": get_chassis_summary_data,
                        "cards": get_chassis_card_data,
                        "ports": get_chassis_port_data,
                        "licensing": get_chassis_licensing_data}
