from models import measure
from collections import namedtuple
import time
import discord
import config


def infr_data_to_md(sqlres: list):
    """Generates a markdown table from infraction data
        
        Parameters:
        sqlres: SQL result
    """

    # Initalize an empty string
    md = ""

    # Check if there are any infractions
    if len(sqlres) < 1:
        md = "No infractions"
        return md

    for inf in sqlres:
        md = f"""{md}
        `{inf[0][:8]}` • **{str(measure.Measure(inf[2]))}** • {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(inf[5])))} • {inf[3]}
        """
    return md


def alt_string_find(bot, alts: tuple):
    y = []
    for alt in alts:
        try:
            id = int(alt)
        except ValueError:
            continue
        u = discord.utils.find(lambda u: u.id == id, bot.get_guild(config.guild).members)
        if u is None:
            y.append(id)
        else:
            y.append(u)
    return tuple(y)


def alt_data_to_md(bot, sqlres: namedtuple):
    """Generates markdown for alt accounts
    Required parameters: 
    - bot:discord.Client = Bot used for ID to member conversion
    - sql_result:tuple = SQL Result (from db.GetAlts)

    Returns:
    markdown:str = Markdown string
    """

    md = ""

    if sqlres is None:
        md = "No alt accounts linked"

    else:
        if sqlres.mainflag:
            md = f"Main account is {sqlres.id}"
        else:
            acc = alt_string_find(bot, sqlres.id)
            for a in acc:
                md = f"""{md}
                - {a}"""
    return md


timeletters = ('s', 'm', 'h', 'd')


def add_time_from_str(string: str = "", btime: int = -1, subtract=False):
    """Adds a duration to an epoch
    
        Parameters:
        string: Input string
        btime:  Sets begin time. Defaults to current time
        decrement: Subtracts the time instead of adding

        Returns:
        newtime:int

        Formatting:
        <duration><s/m/h/d>
        s: seconds
        m: minutes
        h: hours
        d: days
        Example: 1 day = 1d. 15 minutes = 15m
    """
    # No begin time supplied or parsed -1: Set current time
    if btime == -1:
        btime = int(time.time())

    global timeletters
    # check if the letters are present
    if string != "" and any(letter in string for letter in timeletters):
        letterindex = [-1]
        for l in timeletters:
            ind = string.find(l)
            if ind > -1:
                letterindex.append(ind)

        # Sort the index
        letterindex.sort()

        ttime = 0

        # For every index found...
        for i in range(0, len(letterindex)):

            try:
                # parse duration and type
                tme = int(string[letterindex[i] + 1:letterindex[i + 1]])
                lme = string[letterindex[i + 1]:letterindex[i + 1] + 1]

                # Add the result to ttime
                if lme == 's':
                    ttime += tme
                elif lme == 'm':
                    ttime += (tme * 60)
                elif lme == 'h':
                    ttime += (tme * 3600)
                elif lme == 'd':
                    ttime += ttime + (tme * 86400)
            except IndexError:
                # Has reached end
                pass
            except ValueError:
                # User fucked up
                raise TypeError("Could not parse string properly!")

        # Return subtracted time or added time
        if subtract:
            return btime - ttime
        else:
            return btime + ttime
    else:
        raise TypeError("Incorrect formatting used!")


def duration_to_text(string: str):
    """Converts duration formatting to human readable text
    
    Required parameters: 
    - string:str = String to convert
    
    Returns:
    Converted string"""
    t = string
    t = t.replace('s', "s ").replace('m', "min ").replace('h', "h ").replace('d', " days ")
    return t
