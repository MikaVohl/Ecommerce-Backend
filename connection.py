import os
import pyodbc

driver = os.environ['driver']
server = os.environ['server']
database = os.environ['database']
username = os.environ['username']
password = os.environ['password']

def svrconn():
    while True:
        try:
            conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};')
            return conn
        except pyodbc.Error as pe:
            print(pe)
            if pe.args[0] == "08S01":
                try:
                    conn.close()
                except:
                    pass
                conn = None
                continue