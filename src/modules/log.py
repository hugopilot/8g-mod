import discord
import config
import datetime
from datetime import date

async def _log(bot, message, to_channel:bool = False, footertxt=None, color=0xFFFFFF):
    """This function is used to log events from the bot in the console, a logfile and log channel
    
    Parameters:
    bot: bot object
    message: log entry message
    to_channel: If true, the message will print in the log channel set in the config file
    footertxt: Custom embed footer text can be put here
    color: Custom embed color can be put here
    """

    
    # Message being formatted to '[date] message' format 
    m = '[{}] {}'.format(datetime.datetime.now(), message)
    
    # Log entry written to file by opening the file, writing to it and then closing it
    with open(config.logloc, 'a', encoding='utf-8') as log_f:
        log_f.write('{}\n'.format(m))
        log_f.close()

    # print log entry to console
    print(m)

    if(to_channel):
        # Get the right channel to post the log entry in
        ch = bot.get_guild(config.guild).get_channel(config.logch)

        # Generate the embed
        embed=discord.Embed(title="Log", description=m, color=color)

        # Set footertext if not None
        if(footertxt != None):
            embed.set_footer(text=str(footertxt))

        # Finally, send it to the channel
        await ch.send(embed=embed)
        
        # Delete the objects
        del embed
        del ch
