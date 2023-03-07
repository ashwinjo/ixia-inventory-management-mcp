import sqlite3


def _get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def write_data_to_database(table_name=None, records=None, ip_tags_dict=None):
    tags = ""
    conn = _get_db_connection()
    cur = conn.cursor()
    
    #Drop previous table and refresh data
    cur.execute(f"DELETE FROM {table_name}")
    for record in records:
        if table_name == "chassis_summary_records":
            if ip_tags_dict:
                tags = ip_tags_dict.get(record["chassisIp"]) #This is a list
                if tags:
                    tags = ",".join(tags)
                else:
                    tags = ""
            else:
                tags = ""
                
            record.update({"tags": tags })
            
            cur.execute(f"""INSERT INTO {table_name} (ip, chassisSN, controllerSN, type_of_chassis, 
                        physicalCards, status_status, ixOS, ixNetwork_Protocols, ixOS_REST, tags, lastUpdatedAt_UTC, mem_bytes, mem_bytes_total, cpu_pert_usage) VALUES 
                        ('{record["chassisIp"]}', '{record['chassisSerial#']}',
                        '{record['controllerSerial#']}','{record['chassisType']}','{record['physicalCards#']}',
                        '{record['chassisStatus']}',
                        '{record['IxOS']}','{record['IxNetwork Protocols']}','{record['IxOS REST']}','{record['tags']}', 
                        datetime('now'), '{record['mem_bytes']}','{record['mem_bytes_total']}','{record['cpu_pert_usage']}')""")
            
            cur.execute(f"UPDATE user_ip_tags SET tags = '{tags}' where ip = '{record['chassisIp']}'")
        
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
                
                if ip_tags_dict:
                    tags = ip_tags_dict.get(record["chassisIp"]) #This is a list
                    if tags:
                        tags = ",".join(tags)
                    else:
                        tags = ""
                else:
                    tags = ""    
                rcd.update({"tags": tags })
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,cardNumber,serialNumber,cardType,numberOfPorts,tags,lastUpdatedAt_UTC) VALUES 
                            ('{rcd["chassisIp"]}', '{rcd["chassisType"]}', '{rcd["cardNumber"]}','{rcd["serialNumber"]}',
                            '{rcd["cardType"]}','{rcd["numberOfPorts"]}', '{rcd['tags']}', datetime('now'))""")
                
                cur.execute(f"UPDATE user_ip_tags SET tags = '{tags}' where ip = '{rcd['serialNumber']}'")
            
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


def writeTags(ip, tags, type_of_update=None, operation=None):
    updated_tags = ""
    if type_of_update == "chassis":
        table = 'user_ip_tags'
        field = 'ip'
            
            
    if type_of_update == "card":
        table = 'user_card_tags'
        field = 'serialNumber'
        
    conn = _get_db_connection()
    cur = conn.cursor()
    
    # Get Present Tags from DB
    ip_tags_dict = getTagsFromCurrentDatabase(type_of_update)
    currenttags = ip_tags_dict.get(ip) # This is a list    
    new_tags = tags.split(",")
    
   # There is a record present
    if currenttags: 
        if operation == "add":
            updated_tags = ",".join(currenttags + new_tags)
        elif operation == "remove":
            for t in new_tags:
                currenttags.remove(t)
            updated_tags = ",".join(currenttags)
            
        cur.execute(f"UPDATE {table} SET tags = '{updated_tags}' where {field} = '{ip}'")
        cur.execute(f"UPDATE chassis_summary_records SET tags = '{updated_tags}' where ip = '{ip}'")
    else: # New Record
        print(f"INSERT INTO {table} ({field}, tags) VALUES ('{ip}', '{tags}')")
        cur.execute(f"INSERT INTO {table} ({field}, tags) VALUES ('{ip}', '{tags}')")
        
        
    conn.commit()
    cur.close()
    conn.close()
    return "Records successfully updated"
        
def getTagsFromCurrentDatabase(type_of_update=None):
    print(type_of_update)
    ip_tags_dict = {}
    if type_of_update == "chassis":
        table = "user_ip_tags"
        field = "ip"
        
    if type_of_update == "card":
        table = "user_card_tags"
        field = "serialNumber"
    
    conn = _get_db_connection()
    cur = conn.cursor()

    query = f"SELECT * FROM {table};"
    print(query)
    posts = cur.execute(query).fetchall()
    cur.close()
    conn.close()
    for post in posts:
        ip_tags_dict.update({post[field]: post["tags"].split(",")})
    return ip_tags_dict