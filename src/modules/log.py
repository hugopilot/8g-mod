import discord
import config
import datetime


async def log(bot, message, *, to_channel: bool = False, to_log: bool = True, footertxt=None, color=0xFFFFFF, expiry=None):
    """This function is used to log events from the bot in the console, a logfile and log channel
    
    Required parameters:
    - bot: bot object
    - message: log entry message

    Optional parameters:
    - to_channel: If true, the message will print in the log channel set in the config file
    - to_log: If true, the message will be printed in the bot.log file
    - footertxt: Custom embed footer text can be put here
    - color: Defines custom embed color
    - expiry: Auto-deletes log entry from log channel (in seconds)
    """

    if to_log:
        # Message being formatted to '[date] message' format 
        m = '[{}] {}'.format(datetime.datetime.utcnow(), message)

        # Log entry written to file by opening the file, writing to it and then closing it
        with open(config.logloc, 'a', encoding='utf-8') as log_f:
            log_f.write('{}\n'.format(m))
            log_f.close()

        # print log entry to console
        print(m)

    # Message being prepared for log
    m = f'{message}'
    if to_channel:
        # Get the right channel to post the log entry in
        ch = bot.get_guild(config.guild).get_channel(config.logch)

        # Generate the embed
        embed = discord.Embed(title="Log", description=m, color=color, timestamp=datetime.datetime.utcnow())

        # Set footertext if not None
        if footertxt is not None:
            embed.set_footer(text=str(footertxt))

        # Finally, send it to the channel
        await ch.send(embed=embed, delete_after=expiry)

        # Delete the objects
        del embed
        del ch


def errlog(message):
    # Message being formatted to '[date] message' format 
    m = '[{}] {}'.format(datetime.datetime.utcnow(), message)

    # Print to console
    print(m)
    # Log entry written to file by opening the file, writing to it and then closing it
    with open(config.errloc, 'a', encoding='utf-8') as log_f:
        log_f.write('{}\n'.format(m))
        log_f.close()
