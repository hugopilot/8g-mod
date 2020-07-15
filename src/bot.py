# Discord.py library imports
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import time
import traceback

# System libraies imports
import typing
import functools
import asyncio
import datetime
# Source imports
import config
from models import elevatedperms
from models.measure import Measure
from models import errors
from models.colors import COLOR

from modules import db
from modules import log
from modules import markdown
from modules import update
from modules import spam

# Delete default help command
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')


# Global vars
recentrmv = []

# This cog runs every minute. Unmuting members, updating recentban, etc
class minuteupdate(commands.Cog):

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

                guild = bot.get_guild(config.guild)
                mutedr = guild.get_role(config.mutedrole)
                mres = await update.checkmutes()
                # unmute normals
                for case in mres[0]:
                    db.RemoveMuteMember(case)
                    u = guild.get_member(case)
                    if(u == None):
                        await log._log(self.bot, "Cannot lift mute, member probably left", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.WARN.value)
                    else:
                        await u.remove_roles(mutedr, reason ='Automatically lifted (timeout) by bot')
                        await log._log(self.bot, f"Mute on {u} lifted (timeout).", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.ATTENTION_OK.value)
                # unmute errors
                for case in mres[1]:
                    db.RemoveMuteMember(case)
                    u = guild.get_member(case)
                    if(u == None):
                        await log._log(self.bot, "Cannot lift mute, member probably left", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.WARN.value)
                    else:
                        u.remove_roles(mutedr, reason ='Automatically lifted (NULL ERROR) by bot')
                        await log._log(self.bot, f"Mute on {u} lifted (NULL ERROR).", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.ATTENTION_WARN.value)

            except Exception:
                pass
            await asyncio.sleep(60)


bot.add_cog(minuteupdate(bot))
bot.add_cog(spam.AntiSpam(bot))
# Global functions
def inDM(ctx):
    """Checks if a message was sent in DMs
    
    Required parameters:
    - ctx: Discord.Context object"""

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
async def ban(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = "No reason supplied; Pluto Mod Bot"):

    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.Member)):
        # ignore if self
        if(ctx.author == musr):
            return

        # Fail if user is invincible
        if(len([r for r in musr.roles if r.id in config.invincibleroles]) > 0):
            await ctx.send("_🚫 You can't ban invincible users_")
            return

        # Put it in the database
        db.AddInfraction(musr.id, Measure.BAN, reason, ctx.author.id)

        await musr.send(f"You were banned from {ctx.guild} • {reason}")

        # Add it to the recentrmv list
        global recentrmv
        recentrmv.append(musr.id)

        # Use the hammer: ban the user
        await ctx.guild.ban(musr, reason=reason)

        # Log it
        await log._log(bot, f"{musr} was banned by {ctx.author} with reason: {reason}", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)
        
        # Send feedback
        await ctx.send(f"✅ Banned {musr} | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def kick(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.Member)):

        # ignore if self
        if(ctx.author == musr):
            return

        # Fail if user is invincible
        if(len([r for r in musr.roles if r.id in config.invincibleroles]) > 0):
            await ctx.send("_🚫 You can't kick invincible users_")
            return

        # Put it in the database
        db.AddInfraction(musr.id, Measure.KICK, reason, ctx.author.id)

        # Add it to the recentrmv list
        global recentrmv
        recentrmv.append(musr.id)

        await musr.send(f"You were kicked from {ctx.guild} • {reason}")

        # Use the hammer: Kick the user
        await ctx.guild.kick(musr, reason=reason)

        # Log it
        await log._log(bot, f"{musr} was kicked by {ctx.author} with reason: {reason}",to_channel=True,footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was kicked | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def mute(ctx, musr: typing.Union[discord.Member, str] = None, duration:str = "30m", *, reason: str = "No reason supplied"):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.Member)):
        # ignore if self
        if(ctx.author == musr):
            return

        # Fail if user is invincible
        if(len([r for r in musr.roles if r.id in config.invincibleroles]) > 0):
            await ctx.send("_🚫 You can't mute invincible users_")
            return

        # Put it in the database
        db.AddInfraction(musr.id, Measure.MUTE, reason, ctx.author.id)

        # Try to get the role
        mr = ctx.guild.get_role(config.mutedrole)

        # Bot couldn't find the correct role
        if(mr == None):
            raise errors.RoleNotFoundError("Muted role not found!", "Update ID in config file")
            return

        try:
            ti = markdown.add_time_from_str(duration)
            db.SetMuteMember(musr.id, ti)
        except TypeError:
            await ctx.send("Wrong formatting used!")
            return

        # Assign the muted role
        await musr.add_roles(mr, reason=reason)

        await musr.send(f"You were muted in {ctx.guild} for {markdown.duration_to_text(duration)} • {reason}")

        # Log it
        await log._log(bot, f"{musr} was muted by {ctx.author} with reason: {reason}",to_channel=True,footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was muted for {markdown.duration_to_text(duration)} | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def unmute(ctx, musr: typing.Union[discord.Member, str]):
    # Check if the musr object was properly parsed as a User object
    if(isinstance(musr, discord.Member)):
        # ignore if self
        if(ctx.author == musr):
            return
        # Check if muted
        if(not db.CheckMuted(musr.id)):
            await ctx.send("🚫 {musr} is already unmuted!")

        mutedr = ctx.guild.get_role(config.mutedrole)

        db.RemoveMuteMember(musr.id)
        await musr.remove_roles(mutedr, reason =f'Lifted by {ctx.author}')
        await log._log(bot, f"Mute on {musr} lifted by {ctx.author}.",to_channel=True,footertxt=f"User ID: {musr.id}",color=COLOR.ATTENTION_OK.value)
        await ctx.send(f"✅ {musr} was unmuted!")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def warn(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = None):
    # Check if reason is None
    if(reason == None):
        await ctx.send("_🚫 Reason must be supplied!_")
        return

    

    # Check if the musr object was properly parsed as a Member object
    if(isinstance(musr, discord.Member)):
        # ignore if self
        if(ctx.author == musr):
            return

        # Fail if user is invincible
        if(len([r for r in musr.roles if r.id in config.invincibleroles]) > 0):
            await ctx.send("_🚫 You can't warn invincible users_")
            return

        # Put it in the database
        db.AddInfraction(musr.id, Measure.WARN, reason, ctx.author.id)

        # Log it
        await log._log(bot, f"{musr.mention} was warned by {ctx.author.mention} with reason: {reason}",to_channel=True, footertxt=f"User ID: {musr.id}",color=COLOR.ATTENTION_WARN.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was warned | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")

@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def purge(ctx, amount:int = 50):
    # this is a built in command from the library
    await ctx.channel.purge(limit=amount)

    # Log it
    await log._log(bot, f"{ctx.author} used purge command in {ctx.channel.name}, deleted {amount} messages",to_channel=True,footertxt=f"User ID: {ctx.author.id}",color=COLOR.ATTENTION_INFO.value)

#endregion

#region info commands
@bot.command()
async def whois(ctx, musr: typing.Union[discord.Member, str] = None):

    # Embed
    if(isinstance(musr, discord.Member)):
        embed=discord.Embed(title="WHOIS", description=f"{musr.mention}", color=0x469eff)
        embed.set_author(name="Pluto's Shitty Mod Bot")
        embed.set_thumbnail(url=f"{str(musr.avatar_url)}")
        embed.add_field(name="Username", value=f"{musr}", inline=True)
        embed.add_field(name="Registered", value=f"{str(musr.created_at)}", inline=True)
        if(not inDM(ctx)):
            embed.add_field(name="Nickname", value=f"{musr.nick}", inline=True)
            embed.add_field(name="Joined", value=f"{str(musr.joined_at)}", inline=True)
        embed.set_footer(text=f"User ID: {musr.id}")
    if(isinstance(musr, str)):
        embed=discord.Embed(title="WHOIS", description=f"<@{musr}>", color=0x469eff)
        embed.set_author(name="Pluto's Shitty Mod Bot")
    
    

    # Check if the author has elevated permissions
    getter = functools.partial(discord.utils.get, ctx.author.roles)
    if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in elevatedperms.elevated):

        # Get all infractions and convert it into a markdown format
        if(isinstance(musr, str)):
            md = markdown.infr_data_to_md(db.GetAllInfractions(musr))
        else:
            md = markdown.infr_data_to_md(db.GetAllInfractions(musr.id))

        # set the embed
        embed.add_field(name="Infractions", value=f"{md}", inline=False)
    
    
    await ctx.send(embed=embed)

@bot.command()
async def version(ctx):
    await ctx.send(f"✅ Running version: _v{config.version}_")

#endregion

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

    await log._log(bot, f"{user} was banned with reason: {reason}",to_channel=True, footertxt=f"User ID: {user.id}", color=COLOR.ATTENTION_BAD.value)
    
@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def infraction(ctx, id:str, cmd:str):
    
    # Get infraction info from the database
    res = db.GetInfraction(id)
    
    # Error out if nothing is found
    if(len(res) < 1):
        await ctx.send("🚫 Didn't find any infractions")
        return

    # if delete argument was supplied with the command 
    if(cmd == 'delete'):
        # If just one result is found, delete it
        if(len(res) == 1):
            # Delete from the database
            db.DeleteInfraction(res[0][0])

            # Give feedback; log it and exit
            await ctx.send(f"✅ Infraction {res[0][0]} deleted!")
            await log._log(bot, f"{ctx.author.mention} deleted infraction {res[0][0]}", to_channel = True, footertxt=f'User ID: {ctx.author.id}', color=COLOR.ATTENTION_INFO.value)
            return 

    # Create an embed, fill it with data and send it!
    embed=discord.Embed(title="Infractions", description=f"Found {len(res)} result(s). Showing first", color=0x469EFF)
    embed.set_author(name="Pluto's Shitty Mod Bot")
    case = res[0]
        
    embed.add_field(name="GUID", value=f"{case[0]}", inline=True)

    embed.add_field(name="User", value=f"<@{int(case[1])}>", inline=True)
    embed.add_field(name="Type", value=f"{str(Measure(case[2]))}", inline=True)
    embed.add_field(name="Reason", value=f"{case[3]}", inline=True)
    embed.add_field(name="Recorded by", value=f"<@{int(case[4])}>", inline=True)
    embed.add_field(name="Timestamp", value=f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(case[5])))}", inline=True)

    await ctx.send(embed=embed)
    del embed

# This event is risen when a member joins the server
@bot.event
async def on_member_join(member):
    await log._log(bot, f"{member} joined the server!", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.ATTENTION_OK.value)
    if(db.CheckMuted(member.id)):
        # Try to get the role
        mr = member.guild.get_role(config.mutedrole)

        # Bot couldn't find the correct role
        if(mr == None):
            raise errors.RoleNotFoundError("Muted role not found!", "Update ID in config file")
        else:
            # Assign the muted role
            await member.add_roles(mr, reason="Auto-reassigned by Pluto's Shitty Mod Bot")
            await log._log(bot, f"Found mute on {member}, reassigned role!", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.BAD.value)
    
    # Assign roles defined in config.autoroles
    for r in config.autoroles:
        # Bot couldn't find the correct role
        rq = member.guild.get_role(r)
        if(rq == None): 
            raise errors.RoleNotFoundError("{r} could not be found!", "Update ID in config file")
            continue
        await member.add_roles(rq, reason="Auto-assigned by Pluto's Shitty Mod Bot")
        await log._log(bot, f"Auto assigned `{rq}` to {member}", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.INFO.value)

# Logs member updates
@bot.event
async def on_member_update(before, after):
     # Ignore bots
    if(before.bot):
        return

    # Check if the nickname changed. If true: log it
    if(before.nick != after.nick):
        await log._log(bot, f"""{before}'s nickname has been updated
        **Before**:
        {before.nick}
    
        **After**:
        {after.nick}""", to_channel=True, footertxt=f"Message ID: {after.id}; Created at: {before.created_at}", color=COLOR.INFO.value)
    
    # Get a list of the assigned and removed roles
    #newassign = [role for role in after.roles if not after.roles in before.roles]
    #rmvassign = [role for role in before.roles if not before.roles in after.roles]    
    
    # For each newly assigned role, log it
#    if(len(newassign) > 0):
#        for role in newassign:
#            # Ignore '@everyone' role
#            if(role == before.guild.default_role):
#                continue
#            await log._log(bot, f"Role `{role.name}` assigned to {before}", to_channel=True, footertxt=f"User ID: {after.id}", color=COLOR.INFO.value)
    # Do the same for the removed roles
#    if(len(rmvassign) > 0):
#        for role in rmvassign:
#            if(role == before.guild.default_role):
#                continue
#            await log._log(bot, f"Role `{role.name}` removed from {before}", to_channel=True, footertxt=f"User ID: {after.id}", color=COLOR.INFO.value)
               
    
# This event is risen when a member left the server (this can be the cause of kicking too!)
@bot.event
async def on_member_remove(member):
    await log._log(bot, f"Member {member} left", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.ATTENTION_BAD.value)

@bot.event
async def on_message_delete(message):
    # Ignore bots
    if(message.author.bot):
        return
    if(spam.deleting):
        return
    al = message.guild.audit_logs(limit = 3, action = discord.AuditLogAction.message_delete, after = datetime.datetime.utcnow() - datetime.timedelta(seconds = 10))
    re = await al.get(target = message.author)
    if(re == None or re.user == None):
        await log._log(bot, f"**Message from {message.author.mention} deleted in <#{message.channel.id}>**:\n{message.content}",to_channel=True, to_log=False, footertxt=f"Message ID: {message.id}; Created at: {message.created_at}", color=COLOR.BAD.value, expiry = config.sensitive_expiry)
    elif(re.user == bot.user):
        return
    else:
        await log._log(bot, f"**Message from {message.author.mention} deleted in <#{message.channel.id}> by {re.user.mention}**:\n{message.content}",to_channel=True, to_log=False, footertxt=f"Message ID: {message.id}; Created at: {message.created_at}", color=COLOR.BAD.value, expiry = config.sensitive_expiry)
    
@bot.event
async def on_message_edit(before, after):
    # Ignore bots
    if(before.author.bot):
        return
    if(before.content == after.content):
        return
    await log._log(bot, f"""{after.author.mention} edited message in <#{before.channel.id}>:
    
    **Before**:
    {before.content}
    
    **After**:
    {after.content}""", to_channel=True, to_log = False, footertxt=f"Message ID: {after.id}; Created at: {before.created_at}", color=COLOR.INFO.value, expiry = config.sensitive_expiry)

# this is used for spam prevention

@bot.event
async def on_command_error(context, exception):
    # Skip 'command not found errors'
    if(isinstance(exception, commands.errors.CommandNotFound) or isinstance(exception, commands.errors.BadArgument)):
        return
    # Handling Forbidden and NotFound errors
    if(isinstance(exception.original, discord.errors.Forbidden)):
        # Try to send 
        try:
            await context.send("[DISCORD ERROR] HTTP 403")
        except:
            if(isinstance(exception.original, discord.errors.Forbidden)):
                await context.author.send("[DISCORD ERROR] HTTP 403;")
        return
    if(isinstance(exception.original, discord.errors.NotFound)):
        await context.send("[DISCORD ERROR] HTTP 404")
        return
    # General HTTP failures
    if(isinstance(exception.original, discord.errors.HTTPException)):
        await context.send("[DISCORD ERROR] General HTTP error (not 200)")
        return
    if(isinstance(exception.original, discord.ext.commands.UnexpectedQuoteError)):
        await context.send("_Unexpected closing of the string. Error has been logged_")

    ex = traceback.format_exception(type(exception), exception, exception.__traceback__)
    m = """[ERR] """
    for line in ex:
        m = """{}{}""".format(m, line)
    if(context.guild == None):  
        m = f"{m}\nIN DM, thanks to {context.author} ({context.author.id})\n\n"
    else:
        m = f"{m}\nIn {context.guild} ({context.guild.id}), thanks to {context.author} ({context.author.id})\n\n".format(m, context.guild, context.guild.id, context.author, context.author.id)
    log._errlog(m)

    await context.send("Ohoh, something went wrong. Error has been logged")


@bot.command()
async def help(ctx):
    await ctx.author.send("**Help yourself!** Source can be found here: https://github.com/hugopilot/pluto-mod (nah jk but we're too lazy to add help cuz bot is not done yet)")

@bot.command()
async def shutdown(ctx):
    if(any(ctx.author.id == user for user in config.owners)):
        await log._log(bot, f"(SYS) SHUTDOWN COMMAND RECIEVED BY {ctx.author}")
        await ctx.send("✅ Shutting down")
        await bot.logout()

bot.run(config.token)
