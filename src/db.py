import sqlite3
from sqlite3 import Error

import datetime
from datetime import date

import config

# Some basic commands
def connect(file = config.databaseloc):
    try:
        conn = sqlite3.connect(file)
        return conn
    except Error:
        return -1


def close_con(con):
    con.close()

def _sql_escape_string(strr):
    sr = str(strr)
    s = sr.replace("'", "''")
    return s 
# END Basic commands



