import sqlite3
import json

def _get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn


def write_data_to_database(table_name=None, records=None, ip_tags_dict=None):
    tags = ""
    conn = _get_db_connection()
    cur = conn.cursor()
    
    # Clear of old records from database
    if table_name != "chassis_utilization_details":
        cur.execute(f"DELETE FROM {table_name}")
    
    for record in records:
        if table_name == "chassis_summary_details":
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
                        physicalCards, status_status, ixOS, ixNetwork_Protocols, ixOS_REST, tags, lastUpdatedAt_UTC, 
                        mem_bytes, mem_bytes_total, cpu_pert_usage, os) VALUES 
                        ('{record["chassisIp"]}', '{record['chassisSerial#']}',
                        '{record['controllerSerial#']}','{record['chassisType']}','{record['physicalCards#']}',
                        '{record['chassisStatus']}',
                        '{record.get('IxOS', "NA")}','{record.get('IxNetwork Protocols',"NA")}','{record.get('IxOS REST',"NA")}','{record['tags']}', 
                        datetime('now'), '{record.get('mem_bytes', '0')}','{record.get('mem_bytes_total', '0')}','{record.get('cpu_pert_usage', '0')}',
                        '{record['os']}')""")
        
        if table_name == "license_details_records":
            for rcd in record:
                cur.execute(f"""INSERT INTO {table_name} (chassisIp, typeOfChassis, hostId, partNumber, 
                            activationCode, quantity, description, maintenanceDate, expiryDate, isExpired, lastUpdatedAt_UTC) VALUES 
                            ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}',
                            '{rcd["hostId"]}','{rcd["partNumber"]}',
                            '{rcd["activationCode"]}','{str(rcd["quantity"])}','{rcd["description"]}',
                            '{rcd["maintenanceDate"]}','{rcd["expiryDate"]}','{str(rcd["isExpired"])}', datetime('now'))""")
                
        if table_name == "chassis_card_details":
            for rcd in record:
                print(rcd)
                if ip_tags_dict:
                    tags = ip_tags_dict.get(record["chassisIp"]) #This is a list
                    if tags:
                        tags = ",".join(tags)
                    else:
                        tags = ""
                else:
                    tags = ""    
                rcd.update({"tags": tags })
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,cardNumber,serialNumber,cardType,cardState,numberOfPorts,tags,
                            lastUpdatedAt_UTC) VALUES 
                            ('{rcd["chassisIp"]}', '{rcd["chassisType"]}', '{rcd["cardNumber"]}','{rcd["serialNumber"]}',
                            '{rcd["cardType"]}','{rcd["cardState"]}','{rcd["numberOfPorts"]}', '{rcd['tags']}', datetime('now'))""")
            
        if table_name == "chassis_port_details":
            for rcd in record:
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,cardNumber,portNumber,linkState,phyMode,transceiverModel,
                            transceiverManufacturer,owner, speed, type, totalPorts,ownedPorts,freePorts, lastUpdatedAt_UTC) VALUES 
                                ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}', '{rcd["cardNumber"]}','{rcd["portNumber"]}','{rcd.get("linkState", "NA")}',
                                '{rcd.get("phyMode","NA")}','{rcd.get("transceiverModel", "NA")}', '{rcd.get("transceiverManufacturer", "NA")}','{rcd["owner"]}',
                                '{rcd.get("speed", "NA")}','{rcd.get("type", "NA")}','{rcd["totalPorts"]}','{rcd["ownedPorts"]}', '{rcd["freePorts"]}',datetime('now'))""")
                
        if table_name == "chassis_sensor_details":
            for rcd in record:
                unit = rcd["unit"]
                if {rcd["unit"]} ==  "CELSIUS": unit = f'{rcd["value"]} {chr(176)}C'
                if {rcd["unit"]} ==  "AMPERSEND": unit = "AMP"
                cur.execute(f"""INSERT INTO {table_name} (chassisIp,typeOfChassis,sensorType,sensorName,sensorValue,unit,lastUpdatedAt_UTC) VALUES 
                                ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}', '{rcd.get("type", "NA")}','{rcd["name"]}',
                                 '{rcd["value"]}','{unit}', datetime('now'))""")
          
        if table_name == "chassis_utilization_details":
            print({record["lastUpdatedAt_UTC"]})
            cur.execute(f"""INSERT INTO {table_name} (chassisIp,mem_utilization,cpu_utilization,lastUpdatedAt_UTC) VALUES 
                            ('{record["chassisIp"]}', '{record["mem_utilization"]}', '{record["cpu_utilization"]}', '{record["lastUpdatedAt_UTC"]}')""")
            
    cur.close()
    conn.commit()
    conn.close()

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
        cur.execute(f"UPDATE chassis_summary_details SET tags = '{updated_tags}' where ip = '{ip}'")
    else: # New Record
        cur.execute(f"INSERT INTO {table} ({field}, tags) VALUES ('{ip}', '{tags}')")
        
        
    conn.commit()
    cur.close()
    conn.close()
    return "Records successfully updated"
        
def getTagsFromCurrentDatabase(type_of_update=None):
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
    posts = cur.execute(query).fetchall()
    cur.close()
    conn.close()
    for post in posts:
        ip_tags_dict.update({post[field]: post["tags"].split(",")})
    return ip_tags_dict


def getChassistypeFromIp(chassisIp):
    conn = _get_db_connection()
    cur = conn.cursor()
    
    query = f"SELECT type_of_chassis FROM chassis_summary_details where ip = '{chassisIp}';"
    posts = cur.execute(query).fetchone()
    cur.close()
    conn.close()
    if posts:
        return  posts['type_of_chassis']
    return "NA"
    

def write_username_password_to_database(list_of_un_pw):
    conn = _get_db_connection()
    cur = conn.cursor()
    user_pw_dict = []
    cur.execute("DELETE from user_db")
    user_pw_dict = creat_config_dict(list_of_un_pw)
    user_pw_dict = list({v['ip']:v for v in user_pw_dict}.values())
    json_str_data = json.dumps(user_pw_dict)
    q = f"""INSERT INTO user_db (ixia_servers_json) VALUES ('{json_str_data}')"""
    cur.execute(q)
    cur.close()
    conn.commit()
    conn.close()

def read_username_password_from_database():
    conn = _get_db_connection()
    cur = conn.cursor()
    query = f"SELECT * FROM user_db;"
    posts = cur.execute(query).fetchone()
    cur.close()
    conn.close()
    if posts:
        return posts['ixia_servers_json']
    return []


def creat_config_dict(list_of_un_pw):
    config_now = read_username_password_from_database()
    print(config_now)
    # Converting String to List
    config = list_of_un_pw.split("\n")
    if config_now:
        config_now = json.loads(config_now)
        for item in config:
            operation, ip, un, pw = item.split(",")
            if operation == "DELETE":
                for idx, chassis_config in enumerate(config_now):
                    if ip == chassis_config["ip"]:
                        del config_now[idx]
                        print(f"defeted idx {idx}")
                        break
            elif operation == "ADD":
                if ip not in [c["ip"] for c in config_now]:
                    config_now.append({
                                "ip": ip.strip(),
                                "username": un.strip(),
                                "password": pw.strip(),
                            })
            elif operation == "UPDATE":
                pass
    else:
        for item in config:
            operation, ip, un, pw = item.split(",")
            config_now.append({
                "ip": ip.strip(),
                "username": un.strip(),
                "password": pw.strip(),
            })
    print(config_now)
    return config_now

def get_perf_metrics_from_db(ip):
    conn = _get_db_connection()
    cur = conn.cursor()
    query = f"SELECT * FROM chassis_utilization_details where chassisIp='{ip}';"
    posts = cur.execute(query).fetchall()
    cur.close()
    conn.close()
    return posts
    
def write_polling_intervals_into_database(chassis, cards, ports, sensors, licensing, perf):
    conn = _get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE from poll_setting")
    cur.execute(f"""INSERT INTO poll_setting (chassis, cards, ports, sensors, perf, licensing) VALUES 
                ({int(chassis)},{int(cards)},{int(ports)},{int(sensors)},{int(perf)},{int(licensing)})""")
    cur.close()
    conn.commit()
    conn.close()
    
def read_poll_setting_from_database():
    conn = _get_db_connection()
    cur = conn.cursor()
    query = f"SELECT * FROM poll_setting;"
    posts = cur.execute(query).fetchone()
    cur.close()
    conn.close()
    if posts:
        return posts
