import discord
from discord.ext.commands import Cog
import datetime
import asyncio

import collections
from collections import Counter
import re

from modules import log
import config

deleting = False
# Regular expressions for finding urls and emojis
url_pattern = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
emoji_pattern = re.compile(":([\w]*):|([\U0001F1E0-\U0001F1FF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0])")

async def msgtruncator(delq):
    """Deletes all messages provided by a list/tuple
    
    Required parameters:
    delq: 'deletion queue'. List of messages that need to be deleted
    """
    global deleting
    try:
        while(len(delq) > 0):
           deleting = True
           msgl = delq.pop()
           try:
               for x in msgl:
                    await x.delete()
           except discord.errors.NotFound:
               continue
        deleting = False
    except asyncio.CancelledError:
        pass

class AntiSpam(Cog):
    """This cog detects spam and deletes it
    
    Constructor:
    Required parameters:
    - bot: bot object"""

    def __init__(self, bot):
        self.bot = bot
        self.delq = []
        self.prunning = False
    
    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # ignore DM and bots
        if(message.guild == None or message.author.bot):
            return
        # Ignore invincible dudes
        if(len([r for r in message.author.roles if r.id in config.invincibleroles]) > 0):
            return
        
        # Get the message history
        earliest_relevant_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        relevant_messages = [ msg async for msg in message.channel.history(after=earliest_relevant_at, oldest_first=False) if not msg.author.bot ]

        # Check emoji count
        evm = [msg for msg in relevant_messages if len(emoji_pattern.findall(msg.content)) > config.emojitolerance]
        if(len(evm) > 0):
            # add it to delete queue
            self.delq.append(evm)

        # Check number of mentions
        mvm = [msg for msg in relevant_messages if len(msg.mentions) > config.mentiontolerance]
        if(len(mvm) > 0):
            self.delq.append(mvm)

        # Put all messages to delete queue if it exceeds the messaging rate
        rate = datetime.datetime.utcnow() - datetime.timedelta(seconds=config.spamtolerance)
        messages_to_check = [ msg for msg in relevant_messages if msg.created_at > rate ]
        md = [msg for msg in messages_to_check if Counter(msg.author for msg in messages_to_check)[msg.author] > config.spamthreshold]
        if(len(md)>0):
            # There is spam there, create a dict with messages that have the same content but somehow got through first antispam round and add it to the deletion queue
            scm = [msg for msg in messages_to_check if Counter(msg.content for msg in messages_to_check)[msg.content] > 1 and Counter(msg.author for msg in messages_to_check)[msg.author] > 1]
            if(len(scm) > 0):
                self.delq.append(scm)
            self.delq.append(md)

        # Start a seperate thread to delete the messages in the deletion queue
        self.bot.loop.create_task(msgtruncator(self.delq))

        


   

    

