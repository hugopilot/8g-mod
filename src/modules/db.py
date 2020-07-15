# System lib imports
import sqlite3
from sqlite3 import Error
import time
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
    """Escape special characters that could allow SQL injection
    Required parameters:
    - strr: string to check
    
    Returns:
    string(escaped_string)"""
    sr = str(strr)
    s = sr.replace("'", "''")
    return s 
# END Basic commands

def _sql_user_exists(userID:int):
    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format SQL query
    q = f"SELECT * FROM users WHERE id = {userID}"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    if(len(r) > 0):
        return True
    return False

def _sql_get_muted():
    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format SQL query
    q = f"SELECT * FROM users WHERE muted = 1"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    if(len(r) > 0):
        return r
    return False  

def CheckMuted(userID:int):
    """Check if a user is muted
    Required parameters:
    - userID: Discord User ID to check
    
    Returns:
    bool(muted)"""
    res = _sql_get_muted()
    if(res == False):
        return False

    if(any(str(userID) in str(case[0]) for case in res)):
        return True
    return False


def AddInfraction(userID:int, measuretype:measure.Measure, reason:str, author:int):
    """Adds a infraction to the database
    
       Required parameters:
       - userID = Discord ID of the user that disobeyed the rules
       - measuretype = Type of measure enum (see models/measure.py)
       - reason = The reason why the infraction should be recorded
       - author = Discord ID of the user that called the command
    """
    # Create a new GUID
    guid = str(uuid.uuid4())

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Don't trust user input
    usre = _sql_escape_string(reason)

    # Format the SQL Query by putting the arguments into the query
    q = f"INSERT INTO infractions (guid, userID, measure, reason, authorID, epoch) VALUES('{guid}', {userID}, {int(measuretype)}, '{usre}', {author}, {int(time.time())});"

    # Execute the SQL Query
    cu.execute(q)
    c.commit()

    # Disconnect from database
    close_con(c)

def GetAllInfractions(userID:int):
    """Gets all infractions from a user from the database
        
        Required parameters:
        userID = Discord ID of the user
    """

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format SQL query
    q = f"SELECT * FROM infractions WHERE userID = {userID}"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    return r

def GetInfraction(id:str):
    """Finds a infraction by ID
    
        Required parameters:
        id = (Part of) GUID of the infraction

        Returns:
        tuple(infractions)
    """

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Don't trust
    ids = _sql_escape_string(id)

    # Format SQL query
    q = f"SELECT * FROM infractions WHERE guid LIKE '%{ids}%'"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    return r

def SetMuteMember(userID:int, mutelift:int):
    """Mutes a member in the database
    
    Required parameters:
    - userID: Discord ID of the user
    - mutelift: Time when the mute should be lifted (epoch int)"""
    # Create new entry if user doesn't exist in db yet
    if(not _sql_user_exists(userID)):
        # Connect to database
        c = connect()
        cu = c.cursor();

        # Format the SQL Query by putting the arguments into the query
        q = f"INSERT INTO users (id, muted, mutelift) VALUES({userID}, 1, {mutelift});"

        # Execute the SQL Query
        cu.execute(q)
        c.commit()
        close_con(c)

    # Update if entry exists
    else:
        # Connect to database
        c = connect()
        cu = c.cursor();

        # Format the SQL Query by putting the arguments into the query
        q = f"UPDATE users SET muted = 1, mutelift = {mutelift} WHERE id = {userID}"

        # Execute the SQL Query
        cu.execute(q)
        c.commit()
        close_con(c)

def RemoveMuteMember(userID:int):
    """Unmutes a member in the database
    
    Required parameters:
    - userID: Discord ID of the user"""

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format the SQL Query by putting the arguments into the query
    q = f"UPDATE users SET muted = 0, mutelift = NULL WHERE id = {userID}"

    # Execute the SQL Query
    cu.execute(q)
    c.commit()
    close_con(c)

def DeleteInfraction(guid:str):
    """Deletes an infraction from the database

    Required parameters:
    - guid: GUID of the infraction"""

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format the SQL Query by putting the arguments into the query
    q = f"DELETE FROM infractions WHERE GUID = '{guid}'"
    # Execute the SQL Query
    cu.execute(q)
    c.commit()
    close_con(c)