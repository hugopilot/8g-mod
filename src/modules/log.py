import discord
import config
import datetime
from datetime import date

async def _log(bot, message, *, to_channel:bool = False, footertxt=None, color=0xFFFFFF):
    """This function is used to log events from the bot in the console, a logfile and log channel
    
    Parameters:
    bot: bot object
    message: log entry message
    to_channel: If true, the message will print in the log channel set in the config file
    footertxt: Custom embed footer text can be put here
    color: Custom embed color can be put here
    """

    
    # Message being formatted to '[date] message' format 
    m = '[{}] {}'.format(datetime.datetime.utcnow(), message)
    
    # Log entry written to file by opening the file, writing to it and then closing it
    with open(config.logloc, 'a', encoding='utf-8') as log_f:
        log_f.write('{}\n'.format(m))
        log_f.close()

    # print log entry to console
    print(m)

    # Message being prepared for log
    m = f'**{message}**'
    if(to_channel):
        # Get the right channel to post the log entry in
        ch = bot.get_guild(config.guild).get_channel(config.logch)

        # Generate the embed
        embed=discord.Embed(title="Log", description=m, color=color, timestamp=datetime.datetime.utcnow())

        # Set footertext if not None
        if(footertxt != None):
            embed.set_footer(text=str(footertxt))

        # Finally, send it to the channel
        await ch.send(embed=embed)
        
        # Delete the objects
        del embed
        del ch

def _errlog(message):
    # Message being formatted to '[date] message' format 
    m = '[{}] {}'.format(datetime.datetime.utcnow(), message)

    # Print to console
    print(m)
    # Log entry written to file by opening the file, writing to it and then closing it
    with open(config.errloc, 'a', encoding='utf-8') as log_f:
        log_f.write('{}\n'.format(m))
        log_f.close()