import discord
import collections
import re

from modules import log
import config


class SpamMessage():
    """Stripped down version of discord.Message plus a 'duplicate' variable"""
    duplicate = 0
    message = None
    def __init__(self, discmsg:discord.Message, dupe:int = 0):
        self.message = discmsg
        self.duplicate = dupe

deleting = False

# Our 'shift register' for messages. 
message_shift = collections.deque([], 100)

# Regular expressions for finding urls and emojis
url_pattern = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
emoji_pattern = re.compile(":([\w]*):|([\U0001F1E0-\U0001F1FF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0])")

async def check(message:discord.Message):
    # cast to SpamMessage
    cm = SpamMessage(message, 0)

    # Check emoji count
    if(len(emoji_pattern.findall(cm.message.content)) > config.emojitolerance):
        deleting = True
        await cm.message.delete()
        deleting = False

    # Don't check if the register is not filled with anything or the message content == None
    if(len(message_shift) < 1 or cm.message.content == None):
        message_shift.append(cm)
        return

    for i in range(0, len(message_shift)):
        # Check if duplicate
        im = message_shift[i]

        # Check for the same author and channel
        if(cm.message.author == im.message.author and cm.message.channel == im.message.channel):
            #Check the time difference. If > 10 seconds, ignore
            if((abs(cm.message.created_at.timestamp() - im.message.created_at.timestamp()) > 10)):
                message_shift.append(cm)
                return

            # Check if there is a link in both messages or message content is the same
            if(cm.message.content == im.message.content):
                
                # Last check: does the message exceed the tolerance?
                if(im.duplicate >= config.spamtolerance):
                    # delete all messages
                    deleting = True
                    for msg in message_shift:
                        if(msg.message.author == cm.message.author and msg.duplicate > 0):
                            try:
                                await msg.message.delete()
                            except discord.errors.NotFound:
                                continue
                    deleting = False
                    break

                else:
                    # set duplicate
                    cm.duplicate = im.duplicate + 1
                    message_shift.append(cm)
                    break
    del cm
    del im

