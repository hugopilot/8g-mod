# Discord.py library imports
import datetime
import functools
import time
import traceback
# System libraies imports
import typing

# Source imports
import config
import discord
from discord.ext import commands, tasks
from models import elevatedperms
from models import errors
from models.colors import COLOR
from models.measure import Measure
from modules import db
from modules import log
from modules import markdown
from modules import spam
from modules import update

# Delete default help command
bot = commands.Bot(command_prefix=config.prefix)
bot.remove_command('help')

# Bot vars
bot.recentrmv = []


# This cog runs every minute. Unmuting members, updating recentban, etc
class MinuteUpdate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    @tasks.loop(minutes=1)
    async def update_stats(self):
        try:
            await self.bot.wait_until_ready()

            # Empty recentban
            bot.recentrmv = []

            guild = bot.get_guild(config.guild)
            mutedr = guild.get_role(config.mutedrole)
            mres = await update.check_mutes()
            # unmute normals
            for case in mres[0]:
                db.RemoveMuteMember(case)
                u = guild.get_member(case)
                u = guild.get_member(case)
                if u is None:
                    await log.log(self.bot, "Cannot lift mute, member probably left", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.WARN.value)
                else:
                    await u.remove_roles(mutedr, reason='Automatically lifted (timeout) by bot')
                    await log.log(self.bot, f"Mute on {u} lifted (timeout).", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.ATTENTION_OK.value)
            # unmute errors
            for case in mres[1]:
                db.RemoveMuteMember(case)
                u = guild.get_member(case)
                if u is None:
                    await log.log(self.bot, "Cannot lift mute, member probably left", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.WARN.value)
                else:
                    u.remove_roles(mutedr, reason='Automatically lifted (NULL ERROR) by bot')
                    await log.log(self.bot, f"Mute on {u} lifted (NULL ERROR).", to_channel=True, footertxt=f"User ID: {case}", color=COLOR.ATTENTION_WARN.value)

        except Exception:
            pass


bot.add_cog(MinuteUpdate(bot))
bot.add_cog(spam.AntiSpam(bot))


# Global functions
def in_dm(ctx):
    """Checks if a message was sent in DMs
    
    Required parameters:
    - ctx: discord.Context object

    Returns:
    - isDM: str"""
    # If message guild is None, we are in DMs
    if ctx.guild is None:
        return True
    return False


# region mod commands

# This decorator adds the command to the command list
@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
# The function name is the name of the command, unless specified.  
async def ban(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = "No reason supplied; Pluto Mod Bot"):
    # Check if the musr object was properly parsed as a User object
    if isinstance(musr, discord.Member):
        # ignore if self
        if ctx.author == musr:
            return

        # Fail if user is invincible
        if len([r for r in musr.roles if r.id in config.invincibleroles]) > 0:
            return await ctx.send("_🚫 You can't ban invincible users_")

        # Put it in the database
        db.AddInfraction(musr.id, Measure.BAN, reason, ctx.author.id)

        await musr.send(f"You were banned from {ctx.guild} • {reason}")

        # Add it to the recentrmv list
        bot.recentrmv.append(musr.id)

        # Use the hammer: ban the user
        await ctx.guild.ban(musr, reason=reason)

        # Log it
        await log.log(bot, f"{musr} was banned by {ctx.author} with reason: {reason}", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)

        # Send feedback
        await ctx.send(f"✅ Banned {musr} | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def kick(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = None):
    # Check if the musr object was properly parsed as a User object
    if isinstance(musr, discord.Member):

        # ignore if self
        if ctx.author == musr:
            return

        # Fail if user is invincible
        if len([r for r in musr.roles if r.id in config.invincibleroles]) > 0:
            return await ctx.send("_🚫 You can't kick invincible users_")

        # Put it in the database
        db.AddInfraction(musr.id, Measure.KICK, reason, ctx.author.id)

        # Add it to the recentrmv list
        bot.recentrmv.append(musr.id)

        await musr.send(f"You were kicked from {ctx.guild} • {reason}")

        # Use the hammer: Kick the user
        await ctx.guild.kick(musr, reason=reason)

        # Log it
        await log.log(bot, f"{musr} was kicked by {ctx.author} with reason: {reason}", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was kicked | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def mute(ctx, musr: typing.Union[discord.Member, str] = None, duration: str = "30m", *, reason: str = "No reason supplied"):
    # Check if the musr object was properly parsed as a User object
    if isinstance(musr, discord.Member):
        # ignore if self
        if ctx.author == musr:
            return

        alts = db.GetAlts(musr.id)

        # Fail if user is invincible:
        if len([r for r in musr.roles if r.id in config.invincibleroles]) > 0:
            return await ctx.send("_🚫 You can't mute invincible users_")

        # Put it in the database
        db.AddInfraction(musr.id, Measure.MUTE, reason, ctx.author.id)

        # Try to get the role
        mr = ctx.guild.get_role(config.mutedrole)

        # Bot couldn't find the correct role
        if mr is None:
            raise errors.RoleNotFoundError("Muted role not found!", "Update ID in config file")

        try:
            ti = markdown.add_time_from_str(duration)
            db.SetMuteMember(musr.id, ti)
        except TypeError:
            return await ctx.send("Wrong formatting used!")

        # Assign the muted role
        await musr.add_roles(mr, reason=reason)

        await musr.send(f"You were muted in {ctx.guild} for {markdown.duration_to_text(duration)} • {reason}")

        # Log it
        await log.log(bot, f"{musr} was muted by {ctx.author} with reason: {reason}", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_BAD.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was muted for {markdown.duration_to_text(duration)} | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def unmute(ctx, musr: typing.Union[discord.Member, str]):
    # Check if the musr object was properly parsed as a User object
    if isinstance(musr, discord.Member):
        # ignore if self
        if ctx.author == musr:
            return
        # Check if muted
        if not db.CheckMuted(musr.id):
            await ctx.send("🚫 {musr} is already unmuted!")

        mutedr = ctx.guild.get_role(config.mutedrole)

        db.RemoveMuteMember(musr.id)
        await musr.remove_roles(mutedr, reason=f'Lifted by {ctx.author}')
        await log.log(bot, f"Mute on {musr} lifted by {ctx.author}.", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_OK.value)
        await ctx.send(f"✅ {musr} was unmuted!")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def warn(ctx, musr: typing.Union[discord.Member, str] = None, *, reason: str = None):
    # Check if reason is None
    if reason is None:
        return await ctx.send("_🚫 Reason must be supplied!_")

    # Check if the musr object was properly parsed as a Member object
    if isinstance(musr, discord.Member):
        # ignore if self
        if ctx.author == musr:
            return

        # Fail if user is invincible
        if len([r for r in musr.roles if r.id in config.invincibleroles]) > 0:
            return await ctx.send("_🚫 You can't warn invincible users_")

        # Put it in the database
        db.AddInfraction(musr.id, Measure.WARN, reason, ctx.author.id)

        # Log it
        await log.log(bot, f"{musr.mention} was warned by {ctx.author.mention} with reason: {reason}", to_channel=True, footertxt=f"User ID: {musr.id}", color=COLOR.ATTENTION_WARN.value)

        # Send feedback
        await ctx.send(f"✅ {musr} was warned | {reason}")
    else:
        await ctx.send("🚫 Couldn't parse user properly")


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def purge(ctx, amount: int = 50):
    # this is a built in command from the library
    await ctx.channel.purge(limit=amount)

    # Log it
    await log.log(bot, f"{ctx.author} used purge command in {ctx.channel.name}, deleted {amount} messages", to_channel=True, footertxt=f"User ID: {ctx.author.id}", color=COLOR.ATTENTION_INFO.value)


# endregion

# region info commands
@bot.command()
async def whois(ctx, musr: typing.Union[discord.Member, str] = None):
    # Embed
    if isinstance(musr, discord.Member):
        embed = discord.Embed(title="WHOIS", description=f"<@{musr.id}>", color=0x469eff)
        embed.set_author(name="Pluto's Shitty Mod Bot")
        embed.set_thumbnail(url=f"{str(musr.avatar_url)}")
        embed.add_field(name="Username", value=f"{musr}", inline=True)
        embed.add_field(name="Registered", value=f"{str(musr.created_at)}", inline=True)
        if not in_dm(ctx):
            embed.add_field(name="Nickname", value=f"{musr.nick}", inline=True)
            embed.add_field(name="Joined", value=f"{str(musr.joined_at)}", inline=True)

        embed.set_footer(text=f"User ID: {musr.id}")
    else:
        embed = discord.Embed(title="WHOIS", description=f"<@{musr}>", color=0x469eff)
        embed.set_author(name="Pluto's Shitty Mod Bot")

    # Check if the author has elevated permissions
    getter = functools.partial(discord.utils.get, ctx.author.roles)
    if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in
           elevatedperms.elevated):

        # Get all infractions and convert it into a markdown format
        if isinstance(musr, str):
            # if the argument provided was not automatically converted to discord.Member, try to parse it to an id (int) 
            try:
                md1 = markdown.infr_data_to_md(db.GetAllInfractions(int(musr)))
                md2 = markdown.alt_data_to_md(db.GetAlts(int(musr)))
            # Return if casting failed
            except ValueError:
                return await ctx.send("🚫 Couldn't parse user properly")
        else:
            md1 = markdown.infr_data_to_md(db.GetAllInfractions(musr.id))
            md2 = markdown.alt_data_to_md(bot, db.GetAlts(musr.id))

        # set the embed
        embed.add_field(name="Infractions", value=f"{md1}", inline=False)
        embed.add_field(name="Alt info", value=f"{md2}", inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def version(ctx):
    await ctx.send(f"✅ Running version: _v{config.version}_")


# endregion

# This event is risen when a user was banned from the server
@bot.event
async def on_member_ban(guild, user):
    # Check if user was banned with a command (preventing duplicates)
    if user.id in bot.recentrmv:
        return

    # Get reason. Author cannot be tracked (is recorded as 0)
    ban = await guild.fetch_ban(user)
    reason = ban.reason

    # Put it in the database
    db.AddInfraction(user.id, Measure.BAN, reason, 0)

    await log.log(bot, f"{user} was banned with reason: {reason}", to_channel=True, footertxt=f"User ID: {user.id}", color=COLOR.ATTENTION_BAD.value)


@bot.command()
@commands.has_any_role(*elevatedperms.elevated)
async def infraction(ctx, id: str, *, cmd: str = None):
    # Get infraction info from the database
    res = db.GetInfraction(id)

    # Error out if nothing is found
    if len(res) < 1:
        return await ctx.send("🚫 Didn't find any infractions")

    # if delete argument was supplied with the command 
    if cmd == 'delete':
        # If just one result is found, delete it
        if len(res) == 1:
            # Delete from the database
            db.DeleteInfraction(res[0][0])

            # Give feedback; log it and exit
            await ctx.send(f"✅ Infraction {res[0][0]} deleted!")
            return await log.log(bot, f"{ctx.author.mention} deleted infraction {res[0][0]}", to_channel=True, footertxt=f'User ID: {ctx.author.id}', color=COLOR.ATTENTION_INFO.value)

    # Create an embed, fill it with data and send it!
    embed = discord.Embed(title="Infractions", description=f"Found {len(res)} result(s). Showing first", color=0x469EFF)
    embed.set_author(name="Pluto's Shitty Mod Bot")
    case = res[0]

    embed.add_field(name="GUID", value=f"{case[0]}", inline=True)

    embed.add_field(name="User", value=f"<@{int(case[1])}>", inline=True)
    embed.add_field(name="Type", value=f"{str(Measure(case[2]))}", inline=True)
    embed.add_field(name="Reason", value=f"{case[3]}", inline=True)
    embed.add_field(name="Recorded by", value=f"<@{int(case[4])}>", inline=True)
    embed.add_field(name="Timestamp", value=f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(case[5])))}", inline=True)
    if case[6] is not None:
        u = discord.utils.find(lambda u: u.id == int(case[6]), bot.get_guild(config.guild).members)
        if u is not None:
            embed.add_field(name="Alt account", value=f"{u.mention}", inline=True)
        else:
            embed.add_field(name="Alt account", value=f"{case[6]}", inline=True)

    await ctx.send(embed=embed)
    del embed


@bot.command()
async def linkacc(ctx, mainacc: typing.Union[discord.User, str], altacc: typing.Union[discord.User, str]):
    if isinstance(mainacc, str):
        try:
            mainacc = int(mainacc)
        except ValueError:
            # Casting failed
            return
    else:
        mainacc = mainacc.id
    if isinstance(altacc, str):
        try:
            altacc = int(altacc)
        except ValueError:
            # Casting failed
            return
    else:
        altacc = altacc.id

    db.LinkAlt(mainacc, altacc)


# This event is risen when a member joins the server
@bot.event
async def on_member_join(member):
    await log.log(bot, f"{member} joined the server!", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.ATTENTION_OK.value)
    if db.CheckMuted(member.id):
        # Try to get the role
        mr = member.guild.get_role(config.mutedrole)

        # Bot couldn't find the correct role
        if mr is None:
            raise errors.RoleNotFoundError("Muted role not found!", "Update ID in config file")
        else:
            # Assign the muted role
            await member.add_roles(mr, reason="Auto-reassigned by Pluto's Shitty Mod Bot")
            await log.log(bot, f"Found mute on {member}, reassigned role!", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.BAD.value)

    # Assign roles defined in config.autoroles
    for r in config.autoroles:
        # Bot couldn't find the correct role
        rq = member.guild.get_role(r)
        if rq is None:
            raise errors.RoleNotFoundError("{r} could not be found!", "Update ID in config file")
        await member.add_roles(rq, reason="Auto-assigned by Pluto's Shitty Mod Bot")
        await log.log(bot, f"Auto assigned `{rq}` to {member}", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.INFO.value)


# Logs member updates
@bot.event
async def on_member_update(before, after):
    # Ignore bots
    if before.bot:
        return

    # Check if the nickname changed. If true: log it
    if before.nick != after.nick:
        await log.log(bot, f"""{before}'s nickname has been updated
        **Before**:
        {before.nick}
    
        **After**:
        {after.nick}""", to_channel=True, footertxt=f"Message ID: {after.id}; Created at: {before.created_at}", color=COLOR.INFO.value)


# This event is risen when a member left the server (this can be the cause of kicking too!)
@bot.event
async def on_member_remove(member):
    await log.log(bot, f"Member {member} left", to_channel=True, footertxt=f"User ID: {member.id}", color=COLOR.ATTENTION_BAD.value)


@bot.event
async def on_message_delete(message):
    # Ignore bots
    if message.author.bot:
        return
    if spam.deleting:
        return
    al = message.guild.audit_logs(limit=3, action=discord.AuditLogAction.message_delete, after=datetime.datetime.utcnow() - datetime.timedelta(seconds=10))
    re = await al.get(target=message.author)
    if re is None or re.user is None:
        await log.log(bot, f"**Message from {message.author.mention} deleted in <#{message.channel.id}>**:\n{message.content}", to_channel=True, to_log=False, footertxt=f"Message ID: {message.id}; Created at: {message.created_at}", color=COLOR.BAD.value, expiry=config.sensitive_expiry)
    elif re.user == bot.user:
        return
    else:
        await log.log(bot, f"**Message from {message.author.mention} deleted in <#{message.channel.id}> by {re.user.mention}**:\n{message.content}", to_channel=True, to_log=False, footertxt=f"Message ID: {message.id}; Created at: {message.created_at}", color=COLOR.BAD.value, expiry=config.sensitive_expiry)


@bot.event
async def on_message_edit(before, after):
    # Ignore bots
    if before.author.bot:
        return
    if before.content == after.content:
        return
    await log.log(bot, f"""{after.author.mention} edited message in <#{before.channel.id}>:
    
    **Before**:
    {before.content}
    
    **After**:
    {after.content}""", to_channel=True, to_log=False, footertxt=f"Message ID: {after.id}; Created at: {before.created_at}", color=COLOR.INFO.value, expiry=config.sensitive_expiry)


@bot.event
async def on_command_error(context, exception):
    # Skip 'command not found errors'
    if isinstance(exception, commands.errors.CommandNotFound) or isinstance(exception, commands.errors.BadArgument):
        return
    # Handling Forbidden and NotFound errors
    if isinstance(exception.original, discord.errors.Forbidden):
        # Try to send 
        try:
            return await context.send("[DISCORD ERROR] HTTP 403")
        except Exception:
            if isinstance(exception.original, discord.errors.Forbidden):
                return await context.author.send("[DISCORD ERROR] HTTP 403;")
    if isinstance(exception.original, discord.errors.NotFound):
        return await context.send("[DISCORD ERROR] HTTP 404")
    # General HTTP failures
    if isinstance(exception.original, discord.errors.HTTPException):
        return await context.send("[DISCORD ERROR] General HTTP error (not 200)")
    if isinstance(exception.original, discord.ext.commands.UnexpectedQuoteError):
        await context.send("_Unexpected closing of the string. Error has been logged_")

    ex = traceback.format_exception(type(exception), exception, exception.__traceback__)
    m = """[ERR] """
    for line in ex:
        m = """{}{}""".format(m, line)
    if context.guild is None:
        m = f"{m}\nIN DM, thanks to {context.author} ({context.author.id})\n\n"
    else:
        m = f"{m}\nIn {context.guild} ({context.guild.id}), thanks to {context.author} ({context.author.id})\n\n".format(m, context.guild, context.guild.id, context.author, context.author.id)
    log.errlog(m)

    await context.send("Ohoh, something went wrong. Error has been logged")


@bot.command()
async def help(ctx):
    await ctx.author.send("**Help yourself!** Source can be found here: https://github.com/hugopilot/pluto-mod (nah jk but we're too lazy to add help cuz bot is not done yet)")


@bot.command()
async def shutdown(ctx):
    if any(ctx.author.id == user for user in config.owners):
        await log.log(bot, f"(SYS) SHUTDOWN COMMAND RECIEVED BY {ctx.author}")
        await ctx.send("✅ Shutting down")
        await bot.logout()


bot.run(config.token)
