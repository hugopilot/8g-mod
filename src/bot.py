# Discord.py library imports
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions

# System libraies imports
import typing
import functools
# Source imports
import config
from models import elevatedperms
from models import measure
from models.measure import Measure
from modules import db
from modules import log
from modules import markdown

# Delete default help command
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')


# Global vars
recentrmv = []

# This cog runs every minute. Unmuting members, updating recentban, etc
class prupd(commands.Cog):

    def __init__(self, bot):
        self.bot = bot 
        self.updating = self.bot.loop.create_task(self.update_stats())

    async def update_stats(self):
        while not self.bot.is_closed():
            try:
                global recentrmv
                await self.bot.wait_until_ready()

                # Empty recentban
                recentrmv = []

            except Exception:
                # Never let the loop break.
                pass
            await asyncio.sleep(60)
bot.add_cog(prupd(bot))



# Global functions
def inDM(ctx):

    # If message guild is None, we are in DMs
    if(ctx.guild == None):
        return True
    else:
        return False
    return False

#region mod commands

# This decorator adds the command to the command list
@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
# The function name is the name of the command, unless specified.  
async def ban(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = "No reason supplied; Pluto Mod Bot"):

    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.BAN, reason, ctx.author.id)

        await musr.send(f"You were banned from {ctx.guild} • {reason}")

        # Add it to the recentrmv list
        global recentrmv
        recentrmv.append(musr.id)

        # Use the hammer: ban the user
        await ctx.guild.ban(musr, reason=reason)

        # Log it
        await log._log(bot, f"{musr} was banned by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)
        
        # Send feedback
        await ctx.send(f"{musr} was banned | {reason}")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def kick(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.KICK, reason, ctx.author.id)

        # Add it to the recentrmv list
        global recentrmv
        recentrmv.append(musr.id)

        await musr.send(f"You were kicked from {ctx.guild} • {reason}")

        # Use the hammer: Kick the user
        await ctx.guild.kick(musr, reason)

        # Log it
        await log._log(bot, f"{musr} was kicked by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)

        # Send feedback
        await ctx.send(f"{musr} was kicked | {reason}")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def mute(ctx, musr: typing.Union[discord.User, str] = None, duration:str = "30m", *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.MUTE, reason, ctx.author.id)

        # Use the hammer: ban the user
        #ctx.guild.ban(musr, reason)

        # Log it
        await log._log(bot, f"{musr} was muted by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFF0000)

        # Send feedback
        await ctx.send(f"{musr} was muted | {reason}")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def warn(ctx, musr: typing.Union[discord.User, str] = None, *, reason: str = None):
    # Check if reason is None
    if(reason == None):
        await ctx.send("_Reason must be supplied!_")
        return

    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.User)):
        # Put it in the database
        db.AddInfraction(musr.id, Measure.WARN, reason, ctx.author.id)

        # Log it
        await log._log(bot, f"{musr} was warned by {ctx.author} with reason: {reason}", True, f"User ID: {musr.id}", 0xFFD500)

        # Send feedback
        await ctx.send(f"{musr} was warned | {reason}")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def purge(ctx):
    # this is a built in command from the library
    await ctx.channel.purge(limit=amount)

    # Log it
    log._log(bot, f"{ctx.user} used purge command in {ctx.channel.name}", True, f"User ID: {ctx.author.id}", 0x00E8FF)

#endregion

#region info commands
@bot.command()
async def whois(ctx, musr: typing.Union[discord.Member, str] = None):
    embed=discord.Embed(title="WHOIS", description="", color=0x469eff)
    embed.set_author(name="Pluto's Shitty Mod Bot")
    embed.set_thumbnail(url=f"{str(musr.avatar_url)}")
    embed.add_field(name="Username", value=f"{musr}", inline=True)
    embed.add_field(name="Registered", value=f"{str(musr.created_at)}", inline = True)
    if(not inDM(ctx)):
        embed.add_field(name="Nickname", value=f"{musr.nick}", inline=True)
        embed.add_field(name="Joined", value=f"{str(musr.joined_at)}", inline=True)

    # Check if the author has elevated permissions
    getter = functools.partial(discord.utils.get, ctx.author.roles)
    if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in elevatedperms.elevated):

        # Get all infractions and convert it into a markdown format
        md = markdown.infr_data_to_md(db.GetAllInfractions(musr.id))

        # set the embed
        embed.add_field(name="Infractions", value=f"{md}", inline=False)
        
    embed.set_footer(text=f"User ID: {musr.id}")
    await ctx.send(embed=embed)

@bot.command()
async def version(ctx):
    await ctx.send(f"Running version: _v{config.version}_")


# This event is risen when a user was banned from the server
@bot.event
async def on_member_ban(guild, user):
    global recentrmv
    # Check if user was banned with a command (preventing duplicates)
    if(user.id in recentrmv):
        return

    # Get reason. Author cannot be tracked (is recorded as 0)
    ban = await guild.fetch_ban(user)
    reason = ban.reason

    # Put it in the database
    db.AddInfraction(user.id, Measure.BAN, reason, 0)

    await log._log(bot, f"{user} was banned with reason: {reason}", True, f"User ID: {user.id}", 0xFF0000)
    
@bot.event
async def on_member_join(member):
    await log._log(bot, f"{member} joined the server!", True, f"User ID: {member.id}", 0x00FF00)

@bot.event
async def on_member_remove(member):
    await log._log(bot, f"Member {member} left", True, f"User ID: {member.id}", 0x00FF00)

bot.run(config.token)