import asyncio
import re

from redbot.core.bot import Red
from redbot.core import checks, commands


class Giveaway(commands.Cog):
    def __init__(self, bot: Red, dao):
        self.bot = bot
        self.dao = dao
        self.server_config = self.load_server_config()
        self.lock = False

    @commands.guild_only()
    @commands.command(pass_context=True, no_pm=True, help="Join the current giveaway")
    async def giveaway(self, ctx):
        if self.lock:
            return

        this_author = ctx.message.author
        this_channel_id = ctx.message.channel.id
        regular_role = None
        server = self.bot.get_guild(111772771016515584)
        stats = self.dao.get_member_stats("111772771016515584", str(this_author.id))

        # get the regular role
        for r in server.roles:
            if r.id == 345877423142731778:  # Regular
                regular_role = r
                break

        if this_channel_id != 312973523066814467:
            return

        if (
            self.server_config["other"]["giveaway_item"]
            and self.server_config["other"]["giveaway_deadline"]
        ):
            if not self.dao.get_sub_in_giveaway(str(this_author.id)):
                if (
                    "luckboost_3" in stats
                    and stats["luckboost_3"]
                    and regular_role in this_author.roles
                ):
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    stats["luckboost_3"] = False
                    self.dao.update_member_stats(
                        "111772771016515584", str(this_author.id), stats
                    )
                    await ctx.send(
                        this_author.mention
                        + " You joined the giveaway for **{}** with **5x** winning chance for being regular and using a luck ticket! The giveaway will end **{}** and you will be notified if you win. Good Luck! :wink:".format(
                            self.server_config["other"]["giveaway_item"],
                            self.server_config["other"]["giveaway_deadline"],
                        )
                    )
                elif regular_role in this_author.roles:
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    await ctx.send(
                        this_author.mention
                        + " You joined the giveaway for **{}** with **double** winning chance for being regular! The giveaway will end **{}** and you will be notified if you win. Good Luck! :wink:".format(
                            self.server_config["other"]["giveaway_item"],
                            self.server_config["other"]["giveaway_deadline"],
                        )
                    )
                else:
                    self.dao.append_sub_to_giveaway(str(this_author.id), 1)
                    await ctx.send(
                        this_author.mention
                        + " You joined the giveaway for **{}**. The giveaway will end **{}** and you will be notified if you win. Good Luck! :wink:".format(
                            self.server_config["other"]["giveaway_item"],
                            self.server_config["other"]["giveaway_deadline"],
                        )
                    )
            else:
                await ctx.send(
                    this_author.mention + " you already joined the giveaway."
                )
        else:
            await ctx.send("There is no giveaway running right now.")

    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(pass_context=True, no_pm=True, help="Start a new giveaway")
    async def startgiveaway(self, ctx):
        if (
            self.server_config["other"]["giveaway_item"]
            and self.server_config["other"]["giveaway_deadline"]
        ):
            await ctx.send(
                "There is already a giveaway running. Please use !wipegiveaway before you start a new one. (Don't forget to chose a winner before you end!)"
            )
            return
        desc_array = re.findall(r'"([^"]*)"', ctx.message.content)

        if not len(desc_array) == 2:
            await ctx.send(
                'Please set 2 arguments between quotation marks. `!startgiveaway "<item>" "<deadline>"`\nExample: `!startgiveaway "a new GTX2900" "10 days"`'
            )
            return

        self.server_config["other"]["giveaway_item"] = desc_array[0]
        self.server_config["other"]["giveaway_deadline"] = desc_array[1]
        self.dao.update_server_config("111772771016515584", self.server_config)

        await ctx.send(
            "New giveaway was started! Use !giveawaywinner to chose a winner when the time has passed."
        )

    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(pass_context=True, no_pm=True, help="Wipe the giveaway")
    async def wipegiveaway(self, ctx):
        self.dao.wipe_giveaway()
        self.server_config["other"]["giveaway_item"] = ""
        self.server_config["other"]["giveaway_deadline"] = ""
        self.dao.update_server_config("111772771016515584", self.server_config)
        await ctx.send(
            "The giveaway was wiped. You can start a new one with !startgiveaway"
        )

    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(
        pass_context=True, no_pm=True, help="Chose a winner for the current giveaway"
    )
    async def giveawaywinner(self, ctx):
        print("Fetching giveaway winner...")
        if (
            self.server_config["other"]["giveaway_item"]
            and self.server_config["other"]["giveaway_deadline"]
        ):
            win_user = None
            while not win_user:
                winner_id = self.dao.get_random_sub_from_giveaway()
                print("chosen winner id: " + winner_id)
                win_user = self.bot.get_user(int(winner_id))
                print("chosen winner user: " + win_user.name)
            await ctx.send("Shuffling giveaway list...")
            await asyncio.sleep(5)
            await ctx.send("*Shuffling intensifies...*")
            await asyncio.sleep(5)
            await ctx.send("**And the winner is...**")
            await asyncio.sleep(5)
            await ctx.send(
                "Congatulations "
                + win_user.mention
                + " you won **{}**!!!".format(
                    self.server_config["other"]["giveaway_item"]
                )
            )
        else:
            await ctx.send(
                'You have to start a giveaway before you can chose a winner. Please use !startgiveaway "<item>" "<deadline>"'
            )

    @commands.guild_only()
    @checks.mod_or_permissions(manage_messages=True)
    @commands.command(pass_context=True, no_pm=True, help="Lock the giveaway")
    async def lockgiveaway(self, ctx):
        self.lock = True
        await ctx.send(
            "The giveaway has been locked. Unlock again with !unlockgiveaway"
        )

    @commands.guild_only()
    @checks.mod_or_permissions(manage_messages=True)
    @commands.command(pass_context=True, no_pm=True, help="Unlock the giveaway")
    async def unlockgiveaway(self, ctx):
        self.lock = False
        await ctx.send("The giveaway has been unlocked.")

    def load_server_config(self):
        try:
            server_config = self.dao.get_server_config(111772771016515584)
            if not server_config:
                self.dao.add_new_server("111772771016515584")
                server_config = self.dao.get_server_config(111772771016515584)
            return server_config
        except:
            print("Failed reading server_id and/or config")
