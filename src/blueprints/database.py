import mysql.connector

def connect_db ():
    try:
        connection = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")
    except Exception as e:
        raise Exception("Cannot connect to database") 

    return connection
