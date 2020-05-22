# System lib imports
import sqlite3
from sqlite3 import Error
import datetime
from datetime import date
import uuid

# Source imports
import config
from models import measure

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

def AddInfraction(userID:int, measuretype:measure.Measure, reason:str, author:int):
    """Adds a infraction to the database
    
       Parameters:
       userID = Discord ID of the user that disobeyed the rules
       measuretype = Type of measure enum (see models/measure.py)
       reason = The reason why the infraction should be recorded
       author = Discord ID of the user that called the command
    """
    # Create a new GUID
    guid = str(uuid.uuid4())
    # Connect to database
    c = connect()
    cu = c.cursor();

    # Don't trust user input
    usre = _sql_escape_string(reason)

    # Format the SQL Query by putting the arguments into the query
    q = f"INSERT INTO infractions (guid, userID, measure, reason, authorID) VALUES({guid}, {userID}, {str(measuretype)}, {usre}, {author}"

    # Execute the SQL Query
    cu.execute(q)
    c.commit()

    # Disconnect from database
    close_con(c)




