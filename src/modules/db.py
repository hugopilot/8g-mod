# System lib imports
import sqlite3
from sqlite3 import Error
import time
import uuid
from collections import namedtuple

# Source imports
import config
from models import measure


# Some basic commands
def connect(file=config.databaseloc):
    try:
        conn = sqlite3.connect(file)
        return conn
    except Error:
        return -1


def close_con(con):
    con.close()


def _sql_escape_string(strr: str):
    """Escape special characters that could allow SQL injection
    Required parameters:
    - strr:str = string to check
    
    Returns:
    escaped_string:str"""
    sr = str(strr)
    s = sr.replace("'", "''")
    return s


# END Basic commands

def _sql_user_exists(userID: int):
    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format SQL query
    q = f"SELECT * FROM users WHERE id = {userID}"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    if len(r) > 0:
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
    if len(r) > 0:
        return r
    return False


def check_muted(userID: int):
    """Check if a user is muted
    Required parameters:
    - userID = Discord User ID to check
    
    Returns:
    muted:bool"""
    res = _sql_get_muted()
    if not res:
        return False

    if any(str(userID) in str(case[0]) for case in res):
        return True
    return False


def add_infraction(userID: int, measuretype: measure.Measure, reason: str, author: int):
    """Adds a infraction to the database
    
       Required parameters:
       - userID:int = Discord ID of the user that disobeyed the rules
       - measuretype:measure.Measure = Type of measure enum (see models/measure.py)
       - reason:str = The reason why the infraction should be recorded
       - author:int = Discord ID of the user that called the command
    """
    # Check if alts are linked
    ar = get_alts(userID)

    # Don't trust user input
    usre = _sql_escape_string(reason)

    # Create a new GUID
    guid = str(uuid.uuid4())

    if ar is not None and ar.mainflag:
        alt = userID
        userID = ar.id
        # Format the SQL Query by putting the arguments into the query
        q = f"INSERT INTO infractions (guid, userID, measure, reason, authorID, epoch, alt) VALUES('{guid}', {userID}, {int(measuretype)}, '{usre}', {author}, {int(time.time())}, {alt});"
    else:
        q = f"INSERT INTO infractions (guid, userID, measure, reason, authorID, epoch) VALUES('{guid}', {userID}, {int(measuretype)}, '{usre}', {author}, {int(time.time())});"

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Execute the SQL Query
    cu.execute(q)
    c.commit()

    # Disconnect from database
    close_con(c)


def get_all_infractions(userID: int):
    """Gets all infractions from a user from the database
        
        Required parameters:
        userID:int = Discord ID of the user

        Returns:
        result:tuple
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


def get_infraction(id: str):
    """Finds a infraction by ID
    
        Required parameters:
        id = (Part of) GUID of the infraction

        Returns:
        result:tuple
    """

    # Connect to database
    c = connect()
    cu = c.cursor()

    # Don't trust
    ids = _sql_escape_string(id)

    # Format SQL query
    q = f"SELECT * FROM infractions WHERE guid LIKE '%{ids}%'"
    cu.execute(q)
    r = cu.fetchall()
    close_con(c)
    return r


def set_mute_member(userID: int, mutelift: int):
    """Mutes a member in the database
    
    Required parameters:
    - userID:int = Discord ID of the user
    - mutelift:int = Time when the mute should be lifted (epoch int)"""
    # Create new entry if user doesn't exist in db yet
    if not _sql_user_exists(userID):
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


def remove_mute_member(userID: int):
    """Unmutes a member in the database
    
    Required parameters:
    - userID:int = Discord ID of the user"""

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format the SQL Query by putting the arguments into the query
    q = f"UPDATE users SET muted = 0, mutelift = NULL WHERE id = {userID}"

    # Execute the SQL Query
    cu.execute(q)
    c.commit()
    close_con(c)


def delete_infraction(guid: str):
    """Deletes an infraction from the database

    Required parameters:
    - guid:str = GUID of the infraction"""

    # Connect to database
    c = connect()
    cu = c.cursor();

    # Format the SQL Query by putting the arguments into the query
    q = f"DELETE FROM infractions WHERE GUID = '{guid}'"
    # Execute the SQL Query
    cu.execute(q)
    c.commit()
    close_con(c)


def link_alt(mainuser: int, altuser: int):
    # Connect to database
    c = connect()
    cu = c.cursor();

    # Fetch user 
    q = f"SELECT alts FROM users WHERE id = {mainuser}"
    cu.execute(q)
    r = cu.fetchall()

    if len(r) > 0:
        print(r)
        alts = r[0][0]
        if r[0][0] is None:
            alts = ""
        alts = f"{alts}{altuser};"
        q = f"UPDATE users SET alts = '{alts}' WHERE id = {mainuser};"
        cu.execute(q)
        c.commit()
        close_con(c)
        return
    else:
        alts = f"{altuser};"
        # Format the SQL Query by putting the arguments into the query
        q = f"INSERT INTO users (id, alts) VALUES('{mainuser}', '{altuser}');"

        # Execute the SQL Query
        cu.execute(q)
        c.commit()
        close_con(c)
        return


def get_alts(user: int):
    """Returns all linked alt discord id's or returns the main discord id (set with the main flag)
    
    Required parameters:
    - user:int = Discord User ID

    Returns:
    - result:namedtuple(Result, 'id:tuple(int) or int, mainflag:bool') or None
    """
    # Connect to database
    c = connect()
    cu = c.cursor()

    result = namedtuple('result', 'id mainflag')

    # Don't trust
    ids = _sql_escape_string(id)

    # Format SQL query
    q = "SELECT alts FROM users WHERE id = ?"
    cu.execute(q, [user])
    r = cu.fetchone()
    print('PASSED\n\n')
    # The first search didn't find anything
    if r is None or r[0] is None or len(r) < 1:
        q = "SELECT id FROM users WHERE alts LIKE ?"
        cu.execute(q, [f"%{user}%"])
        r = cu.fetchone()

        if r is None or len(r) < 1:
            return None

        return result(int(r[0]), True)
    print(r)
    ids = r[0].split(';')
    print(ids)
    ids.remove('')
    return result((int(res) for res in ids), False)
