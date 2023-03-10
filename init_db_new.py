"""This script will poll all the chassis data every 5 minutes and write it into the database.

Tables:

chassis_summary_details
chassis_card_details
chassis_port_details
chassis_license_details

chassis_cpu_utilization
chassis_memory_utilization
"""

import sqlite3
from sqlite3 import Error
import db_queries


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
        c.close()
        conn.close()
    except Error as e:
        print(e)


def create_data_tables():
    database = "inventory.db"            
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        
        create_table(conn, db_queries.create_usenname_password_table)
        
        create_table(conn, db_queries.create_chassis_summary_sql)
        create_table(conn, db_queries.create_card_details_records_sql)
        create_table(conn, db_queries.create_port_details_records_sql)
        create_table(conn, db_queries.create_license_details_records_sql)
        
        create_table(conn, db_queries.create_ip_tags_sql)
        create_table(conn, db_queries.create_card_tags_sql)
        create_table(conn, db_queries.create_perf_metrics_sql)

create_data_tables()