import sqlite3


def _get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def write_data_to_database(table_name=None, records=None, ip_tag_list=None):
    conn = _get_db_connection()
    cur = conn.cursor()
    
    #Drop previous table and refresh data
    cur.execute(f"DELETE FROM {table_name}")
    print("XXXXXXXXX")
    print(records)
    
    # [['10.36.236.121', 'XGS12-S0250241', '096061', 'Ixia_XGS12-HSL', '4', 'UP', '9.30.3001.12 ', '9.30.2212.1', '1.8.1.10']]
    for record in records:
        if table_name == "chassis_summary_records":
            record = record+ip_tag_list.get(record[0], ["NoTags"])
            cur.execute(f"""INSERT INTO {table_name} (ip, chassisSN, controllerSN, type_of_chassis, 
                        physicalCards, status_status, ixOS, ixNetwork_Protocols, ixOS_REST, tags, lastUpdatedAt_UTC) VALUES 
                        ('{record[0]}', '{record[1]}','{record[2]}','{record[3]}','{record[4]}','{record[5]}','{record[6]}',
                        '{record[7]}','{record[8]}','{record[9]}', datetime('now'))""")
            
        if table_name == "license_details_records":
            for rcd in record:
                cur.execute(f"""INSERT INTO {table_name} (chassisIp, typeOfChassis, hostId, partNumber, 
                            activationCode, quantity, description, maintenanceDate, expiryDate, isExpired, lastUpdatedAt_UTC) VALUES 
                            ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}',
                            '{rcd["hostId"]}','{rcd["partNumber"]}',
                            '{rcd["activationCode"]}','{str(rcd["quantity"])}','{rcd["description"]}',
                            '{rcd["maintenanceDate"]}','{rcd["expiryDate"]}','{str(rcd["isExpired"])}', datetime('now'))""")
                
        if table_name == "cards_details_records":
            for rcd in record:
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,cardNumber,serialNumber,cardType,numberOfPorts, lastUpdatedAt_UTC) VALUES 
                            ('{rcd["chassisIp"]}', '{rcd["chassisType"]}', '{rcd["cardNumber"]}','{rcd["serialNumber"]}',
                            '{rcd["cardType"]}','{rcd["numberOfPorts"]}', datetime('now'))""")
                
        if table_name == "port_details_records":
            for rcd in record:
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,cardNumber,portNumber,phyMode,transceiverModel,
                            transceiverManufacturer,owner,totalPorts,ownedPorts,freePorts, lastUpdatedAt_UTC) VALUES 
                                ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}', '{rcd["cardNumber"]}','{rcd["portNumber"]}',
                                '{rcd.get("phyMode","NA")}','{rcd["transceiverModel"]}', '{rcd["transceiverManufacturer"]}','{rcd["owner"]}',
                                '{rcd["totalPorts"]}','{rcd["ownedPorts"]}', '{rcd["freePorts"]}',datetime('now'))""")
            
    cur.close()
    conn.commit()
    conn.close()
    return "records written to "+table_name
    


def read_data_from_database(table_name=None):
    conn = _get_db_connection()
    cur = conn.cursor()
    records = cur.execute(f"SELECT * FROM {table_name}").fetchall()
    cur.close()
    conn.close()
    return records


def _writeTags(ip, tags, operation=None):
    str_currenttags = ""
    ip_tags_dict = _getTagsFromCurrentDatabase()
    currenttags = ip_tags_dict.get(ip)
    new_tags =  tags.split(",")
   
    conn = _get_db_connection()
    cur = conn.cursor()
    if currenttags: # There is a record present
        if operation == "add":
            str_currenttags = ",".join(currenttags+new_tags)
        elif operation == "remove":
            for t in new_tags:
                currenttags.remove(t)
            str_currenttags = ",".join(currenttags)
        cur.execute(f"UPDATE user_ip_tags SET tags = '{str_currenttags}' where ip = '{ip}'")
    else: # New Record
        cur.execute(f"INSERT INTO user_ip_tags (ip, tags) VALUES ('{ip}', '{tags}')")
    conn.commit()
    cur.close()
    conn.close()
    return "Records successfully updated"
        
def _getTagsFromCurrentDatabase():
    ip_tags_dict = {}
    conn = _get_db_connection()
    cur = conn.cursor()
    posts = cur.execute(f"SELECT * FROM user_ip_tags").fetchall()
    cur.close()
    conn.close()
    for post in posts:
        ip_tags_dict.update({post["ip"]: post["tags"].split(",")})
    return ip_tags_dict