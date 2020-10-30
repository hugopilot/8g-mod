from modules import db
import discord
import time
import config


class Infraction:
    def __init__(self, user_id: int, measure: measure.Measure, reason: str, author_id: int):
        """

        :param user_id: int
        :param measure: measure.Measure
        :param reason: str
        :param author_id: int
        """
        self.user_id: int = user_id
        self.measure: measure.Measure = measure
        self.reason: str = reason
        self.author_id: id = author_id
        self._infraction = None

        # Get infraction info from the database
        res = db.GetInfraction(self.user_id)

        # Error out if nothing is found
        if len(res) < 1:
            # return await ctx.send("🚫 Didn't find any infractions")
            self._infraction = "🚫 Didn't find any infractions"
        else:
            # Create an embed, fill it with data and send it!
            embed = discord.Embed(
                title="Infractions", description=f"Found {len(res)} result(s). Showing first", color=0x469EFF)
            embed.set_author(name="Pluto's Shitty Mod Bot")
            case = res[0]

            embed.add_field(name="GUID", value=f"{case[0]}", inline=True)

            embed.add_field(
                name="User", value=f"<@{int(case[1])}>", inline=True)
            embed.add_field(
                name="Type", value=f"{str(measure.Measure(case[2]))}", inline=True)
            embed.add_field(name="Reason", value=f"{case[3]}", inline=True)
            embed.add_field(name="Recorded by",
                            value=f"<@{int(case[4])}>", inline=True)
            embed.add_field(
                name="Timestamp", value=f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(case[5])))}", inline=True)
            if case[6] is not None:
                u = discord.utils.find(lambda u: u.id == int(
                    case[6]), bot.get_guild(config.guild).members)
                if u is not None:
                    embed.add_field(name="Alt account",
                                    value=f"{u.mention}", inline=True)
                else:
                    embed.add_field(name="Alt account",
                                    value=f"{case[6]}", inline=True)

            # await ctx.send(embed=embed)
            self._infraction = embed
            del embed

    def __str__(self):
        """
        :returns discord.Embed || str
        """
        return self._infraction
