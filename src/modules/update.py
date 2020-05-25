from modules import db
import time
import discord

async def checkmutes():
    """This function checks if there are mutes to be lifed in the database"""
    r = db._sql_get_muted()
    users = []
    erusr = []
    ctime = int(time.time())
    for case in r:
        try:
            if(int(case[2]) < ctime):
                users.append(int(case[0]))
        # This should never happen. Broken code will release mutes
        except ValueError:
            erusr.append(int(case[0]))
    return (users, erusr)

