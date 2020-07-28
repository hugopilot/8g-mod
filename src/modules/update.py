from modules import db
import time


async def check_mutes():
    """This function checks if there are mutes to be lifed in the database"""
    # Get all muted users from the database
    r = db._sql_get_muted()

    # Define two lists: users and erusr. Difference being that if internal errors occured the user will be put in
    # erusr and automatically unmuted
    users = []
    erusr = []

    # Get current epoch
    ctime = int(time.time())

    # Check each 'case'
    for case in r:
        try:
            # If the current time is more than the expiry time, unmute the user
            if int(case[2]) < ctime:
                users.append(int(case[0]))

        # This error should never occur. Broken code will release mutes
        except ValueError:
            erusr.append(int(case[0]))

    # Return a list of users to be unmuted
    return users, erusr
