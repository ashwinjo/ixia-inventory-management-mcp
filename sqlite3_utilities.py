import sqlite3


def _get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def write_data_to_database(table_name=None, records=None, ip_tag_list=None):
    conn = _get_db_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name}")
    # [['10.36.236.121', 'XGS12-S0250241', '096061', 'Ixia_XGS12-HSL', '4', 'UP', '9.30.3001.12 ', '9.30.2212.1', '1.8.1.10']]
    for record in records:
        if table_name == "chassis_summary_records":
            record = record+ip_tag_list.get(record[0], ["NoTags"])
            cur.execute(f"""INSERT INTO {table_name} (ip, chassisSN, controllerSN, type_of_chassis, 
                        physicalCards, status_status, ixOS, ixNetwork_Protocols, ixOS_REST, tags) VALUES 
                        ('{record[0]}', '{record[1]}','{record[2]}','{record[3]}','{record[4]}','{record[5]}','{record[6]}',
                        '{record[7]}','{record[8]}','{record[9]}')""")
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

def process_data_to_be_written():
    pass
