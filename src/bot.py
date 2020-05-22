# Discord.py library imports
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions

# System libraies imports
import typing

# Source imports
import config
from models import elevatedperms
from models import measure
from measure import Measure
from modules import db
from modules import log

# Delete default help command
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')

# This decorator adds the command to the command list
@bot.command()
@commands.has_any_role(elevatedperms.admin, elevatedperms.moderator)
# The function name is the name of the command, unless specified.  
async def ban(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = "No reason supplied; Pluto Mod Bot"):

    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.BAN, reason, ctx.author.id)

        # Use the hammer: ban the user
        ctx.guild.ban(musr, reason)

        # Log it
        log._log(bot, f"{musr} was banned by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)
        

@bot.command()
async def kick(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.KICK, reason, ctx.author.id)

        # Use the hammer: Kick the user
        ctx.guild.kick(musr, reason)

        # Log it
        log._log(bot, f"{musr} was kicked by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)

@bot.command()
async def mute(ctx, musr: typing.Union[discord.User, str] = None, duration:str = "30m", *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.MUTE, reason, ctx.author.id)

        # Use the hammer: ban the user
        ctx.guild.ban(musr, reason)

        # Log it
        log._log(bot, f"{musr} was muted by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)

@bot.command()
async def warn(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    # Check if reason is None
    if(reason == None):
        ctx.send("_Reason must be supplied!_")
        return

    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.WARN, reason, ctx.author.id)

        # Log it
        log._log(bot, f"{musr} was warned by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFFD500)

@bot.command()
async def purge(ctx):
    # this is a built in command from the library
    await ctx.channel.purge(limit=amount)

@bot.command()
async def whois(ctx, musr: typing.Union[discord.User, str] = None):
    pass

bot.run(config.token)