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
                                tags TEXT
                                );"""
                                
                                
    create_chassis_cards_summary_sql = """CREATE TABLE IF NOT EXISTS chassis_summary_records (
                                            ip VARCHAR(255) NOT NULL,
                                            chassisSN TEXT,
                                            controllerSN TEXT,
                                            type_of_chassis TEXT,
                                            physicalCards TEXT,
                                            status_status TEXT,
                                            ixOS TEXT,
                                            ixNetwork_Protocols TEXT,
                                            ixOS_REST TEXT,
                                            tags TEXT
                                            );"""

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, "DROP TABLE chassis_summary_records")
        create_table(conn, create_ip_tags_sql)
        # create tasks table
        create_table(conn, create_chassis_summary_sql)
        time.sleep(5)
    else:
        print("Error! cannot create the database connection.")
        
main()