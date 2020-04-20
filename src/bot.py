import discord
import config
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import typing


# Delete default help command
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')

# This decorator adds the command
@bot.command()
# The function name is the name of the command, unless specified.  
async def ban(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    pass

@bot.command()
async def kick(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    pass

@bot.command()
async def mute(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    pass

@bot.command()
async def whois(ctx, musr: typing.Union[discord.User, str] = None):
    pass

