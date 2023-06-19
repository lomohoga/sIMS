import mysql.connector

from src.blueprints.exceptions import DatabaseConnectionError

def connect_db ():
    try:
        connection = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")
    except Exception as e:
        raise DatabaseConnectionError 

    return connection
