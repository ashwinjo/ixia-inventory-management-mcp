import sqlite3
from sqlite3 import Error
import time


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def main():
    database = "database.db"

    create_ip_tags_sql = """CREATE TABLE IF NOT EXISTS user_ip_tags (
                                    ip VARCHAR(255) NOT NULL,
                                    tags TEXT
                                    );"""
                                    
    create_card_tags_sql = """CREATE TABLE IF NOT EXISTS user_card_tags (
                                    serialNumber VARCHAR(255) NOT NULL,
                                    tags TEXT
                                    );"""

    create_chassis_summary_sql = """CREATE TABLE IF NOT EXISTS chassis_summary_records (
                                ip VARCHAR(255) NOT NULL,
                                chassisSN TEXT,
                                controllerSN TEXT,
                                type_of_chassis TEXT,
                                physicalCards TEXT,
                                status_status TEXT,
                                ixOS TEXT,
                                ixNetwork_Protocols TEXT,
                                ixOS_REST TEXT,
                                tags TEXT,  
                                lastUpdatedAt_UTC TEXT,
                                mem_bytes TEXT, 
                                mem_bytes_total TEXT, 
                                cpu_pert_usage TEXT
                                );"""
                                
                                
    create_license_details_records_sql = """CREATE TABLE IF NOT EXISTS license_details_records (
                                            'chassisIp'VARCHAR(255) NOT NULL,
                                            'typeOfChassis' TEXT,
                                            'hostId' TEXT,
                                            'partNumber' TEXT,
                                            'activationCode' TEXT,
                                            'quantity' TEXT,
                                            'description' TEXT,
                                            'maintenanceDate' TEXT,
                                            'expiryDate' TEXT,
                                            'isExpired' TEXT,
                                            'lastUpdatedAt_UTC' TEXT
                                            );"""
                                            
    create_card_details_records_sql = """CREATE TABLE IF NOT EXISTS cards_details_records (
                                            'chassisIp' VARCHAR(255) NOT NULL,
                                            'typeOfChassis' TEXT,
                                            'cardNumber' TEXT,
                                            'serialNumber' TEXT,
                                            'cardType' TEXT,
                                            'numberOfPorts' TEXT, 
                                            'tags' TEXT, 
                                            'lastUpdatedAt_UTC' TEXT
                                            );"""
                                            
    create_port_details_records_sql = """CREATE TABLE IF NOT EXISTS port_details_records (
                                            'chassisIp' VARCHAR(255) NOT NULL,
                                            'typeOfChassis' TEXT,
                                            'cardNumber' TEXT,
                                            'portNumber' TEXT,
                                            'phyMode' TEXT,
                                            'transceiverModel' TEXT,
                                            'transceiverManufacturer' TEXT,
                                            'owner' TEXT,
                                            'totalPorts' TEXT,  
                                            'ownedPorts' TEXT,
                                            'freePorts' TEXT,
                                            'lastUpdatedAt_UTC' TEXT
                                            );"""
                                    
    drop_ip_tags_sql = "DROP TABLE IF EXISTS user_ip_tags" 
    drop_card_tags_sql = "DROP TABLE IF EXISTS user_card_tags" 
    
    
    drop_chassis_summary_sql = "DROP TABLE IF EXISTS chassis_summary_records" 
    drop_license_details_sql = "DROP TABLE IF EXISTS license_details_records" 
    drop_card_details_sql = "DROP TABLE IF EXISTS cards_details_records" 
    drop_create_port_details_sql = "DROP TABLE IF EXISTS port_details_records" 
                                            
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, drop_chassis_summary_sql)
        create_table(conn, drop_license_details_sql)
        create_table(conn, drop_card_details_sql)
        create_table(conn, drop_create_port_details_sql)
        
         
                 
        create_table(conn, create_ip_tags_sql)
        create_table(conn, create_card_tags_sql)
        create_table(conn, create_chassis_summary_sql)
        create_table(conn, create_license_details_records_sql)
        create_table(conn, create_card_details_records_sql)
        create_table(conn, create_port_details_records_sql)
        time.sleep(5)
    else:
        print("Error! cannot create the database connection.")