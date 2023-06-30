import mysql.connector

from src.blueprints.exceptions import DatabaseConnectionError

def connect_db ():
    try:
        connection = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims", sql_mode = "STRICT_ALL_TABLES,NO_ENGINE_SUBSTITUTION")
    except Exception as e:
        raise DatabaseConnectionError 

    return connection
