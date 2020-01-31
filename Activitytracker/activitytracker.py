import datetime
import pprint
import discord
import asyncio

from redbot.core.bot import Red
from redbot.core import commands
from redbot.core import bank

pp = pprint.PrettyPrinter(indent=4)


class ActivityTracker(commands.Cog):
    """Custom activity tracker"""

    def __init__(self, bot: Red, dao):
        self.bot = bot
        self.dao = dao

        # Adjustable settings
        # ------------------------------------------------
        self.guild_id = 111772771016515584
        self.sub_role_id = 111789209924190208
        self.regular_role_id = 345877423142731778
        self.listening_channel_ids = [
            111772771016515584,
            117297689044975618,
            308668265817964544,
            309318262213312512,
            296969400110678017,
        ]

        # how many messages are needed in an hour for it to be credited
        self.min_msgs_per_hour = 1

        # if he wrote enough messages this hour, the hour will be credited with this many points
        self.hourly_credit = 8

        # if user reached daily max msgs he will get this many points
        self.day_limit_credit = 10

        # maximum hours(msgs) that can be credited per day
        self.daily_max_msgs = 12

        # if user can't keep up this many credited hours per week he loses the role
        self.min_msgs_per_week = 20

        # needed points for role
        self.min_regular_points = 2000
        # ------------------------------------------------

        # Setup Discord py
        self.guild = self.bot.get_guild(self.guild_id)

        self.regular_role = None
        self.sub_role = None
        self.inactives_updated = True  # TODO set false if update is needed

    def __unload(self):
        pass

    def load_roles(self):
        self.regular_role = self.guild.get_role(self.regular_role_id)
        self.regular_role = self.guild.get_role(self.sub_role_id)
        return bool(self.regular_role) and bool(self.regular_role)

    async def activity_listener(self, message):
        if (
            isinstance(message.channel, discord.DMChannel)
            or message.author == self.bot.user
        ):
            return

        author = message.author

        if not self.load_roles():
            print("Error: Roles not found")
            return

        if not self.inactives_updated:
            print("Running inactives task")
            await self.update_inactives()

        # remove regular role if this user is not subbed anymore
        if self.sub_role not in author.roles and self.regular_role in author.roles:
            await author.remove_roles(self.regular_role)

        elif (
            self.sub_role in author.roles
            and message.channel.id in self.listening_channel_ids
        ):
            now = datetime.datetime.now()
            this_stats = self.dao.get_member_stats(str(self.guild_id), author.id)

            # create empty stats if new user
            if "activity_stats" not in this_stats:
                this_stats["activity_stats"] = {}
            if "w_last_check" not in this_stats["activity_stats"]:
                this_stats["activity_stats"]["w_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "msg_count": 0,
                }
            if "d_last_check" not in this_stats["activity_stats"]:
                this_stats["activity_stats"]["d_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "period_credited": False,
                    "msg_count": 0,
                }
            if "h_last_check" not in this_stats["activity_stats"]:
                this_stats["activity_stats"]["h_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "period_credited": False,
                    "msg_count": 0,
                }
            ass = this_stats["activity_stats"]

            # ---------------------------------------
            h_delta_to_now = now - datetime.datetime.strptime(
                ass["h_last_check"]["period"], "%Y-%m-%d %H:%M:%S"
            )
            d_delta_to_now = now - datetime.datetime.strptime(
                ass["d_last_check"]["period"], "%Y-%m-%d %H:%M:%S"
            )

            # reset stats if the hour ended
            if h_delta_to_now.seconds > 3600:
                ass["h_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "period_credited": False,
                    "msg_count": 0,
                }

            # reset stats if the day ended
            if d_delta_to_now.days >= 1:
                ass["d_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "period_credited": False,
                    "msg_count": 0,
                }

            # ----------------------------------------------------------
            # process the hourly point credit
            # ----------------------------------------------------------
            # increase count if we are inside the hourly period and points haven't been credited and daily max hasn't been exceeded
            if (
                h_delta_to_now.seconds <= 3600
                and not ass["h_last_check"]["period_credited"]
                and not ass["d_last_check"]["period_credited"]
            ):
                ass["h_last_check"]["msg_count"] += 1

                # credit the period if enough messages
                if ass["h_last_check"]["msg_count"] >= self.min_msgs_per_hour:
                    balance = await bank.get_balance(author)
                    # deposit points for being active this hour
                    await bank.set_balance(author, balance + self.hourly_credit)
                    ass["h_last_check"]["period_credited"] = True
                    ass["d_last_check"]["msg_count"] += 1

                    print(
                        author.display_name
                        + " received hourly credit (balance from "
                        + str(balance)
                        + " to "
                        + str(balance + self.hourly_credit)
                        + ")"
                    )
                    # print("Stats: ")
                    # pp.pprint(ass)
                    # print("Triggermessage: \"" + message.content + "\" from "+message.channel.name)

                    # lock for this day if daily limit reached
                    if ass["d_last_check"]["msg_count"] >= self.daily_max_msgs:
                        ass["d_last_check"]["period_credited"] = True
                        # up daily gain to 100
                        await bank.set_balance(author, balance + self.day_limit_credit)

                        print(
                            author.display_name
                            + " reached daily limit (balance from "
                            + str(balance)
                            + " to "
                            + str(balance + self.day_limit_credit)
                            + ")"
                        )
                        # print("\nStats:")
                        # pp.pprint(ass)
                        # print("\nTrigger msg: \n\"" + message.content + "\" from "+message.channel.name)

            # apply regular role if user reached 2k points
            if (
                await bank.get_balance(author) >= self.min_regular_points
                and self.regular_role not in author.roles
            ):
                await author.add_roles(
                    self.regular_role,
                    reason="User reached " + str(self.min_regular_points) + " points",
                )
                print(
                    author.display_name
                    + " reached "
                    + str(self.min_regular_points)
                    + " points and received the regular role"
                )

            # ---------------------------------------------------------
            # process weekly period to see if they keep their roles
            # ---------------------------------------------------------
            w_delta_to_now = now - datetime.datetime.strptime(
                ass["w_last_check"]["period"], "%Y-%m-%d %H:%M:%S"
            )
            # pp.pprint(ass)
            # print("weekdelta = " +  str(w_delta_to_now.days))
            # weekly period ended
            if w_delta_to_now.days > 7:
                # remove regular role if he wasn't active enough
                if ass["w_last_check"]["msg_count"] < self.min_msgs_per_week:
                    if self.regular_role in author.roles:
                        await author.remove_roles(
                            self.regular_role, reason="Low user activity"
                        )
                        print(
                            "Removed regular role from "
                            + author.display_name
                            + " because weekly count was only "
                            + str(ass["w_last_check"]["msg_count"])
                        )

                # reset the weekly stats
                this_stats["activity_stats"] = {}
                this_stats["activity_stats"]["w_last_check"] = {
                    "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "msg_count": 0,
                }
            # increase count if we are still inside the weekly period
            else:
                ass["w_last_check"]["msg_count"] += 1

            self.dao.update_member_stats(
                str(self.guild_id), message.author.id, this_stats
            )

    async def update_inactives(self):
        print("Running inactivity update...")
        self.inactives_updated = True

        if not self.load_roles():
            print("Error: Roles not found")
            return

        for member in self.regular_role.members:
            print("Fetching " + str(member))
            this_stats = self.dao.get_member_stats(str(self.guild_id), member.id)
            if "activity_stats" in this_stats:
                ass = this_stats["activity_stats"]
                now = datetime.datetime.now()
                w_delta_to_now = now - datetime.datetime.strptime(
                    ass["w_last_check"]["period"], "%Y-%m-%d %H:%M:%S"
                )

                if w_delta_to_now.days > 7:
                    # remove regular role if he wasn't active enough
                    if ass["w_last_check"]["msg_count"] < self.min_msgs_per_week:
                        if self.regular_role in member.roles:
                            await member.remove_roles(
                                self.regular_role, reason="Low user activity"
                            )
                            print(
                                "Removed regular role from "
                                + member.display_name
                                + " because weekly count was only "
                                + str(ass["w_last_check"]["msg_count"])
                            )
                    # reset the weekly stats
                    this_stats["activity_stats"] = {}
                    this_stats["activity_stats"]["w_last_check"] = {
                        "period": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "msg_count": 0,
                    }

                self.dao.update_member_stats(str(self.guild_id), member.id, this_stats)
                # await asyncio.sleep(0.1)
        print("Inactivity update finished")

    # @commands.command(pass_context=True, no_pm=False, help="")
    # async def activitydebug(self, ctx, user: discord.Member):
    #     author = ctx.message.author
    #
    #     # if self.sub_role not in user.roles:
    #     #    return
    #
    #     this_stats = self.dao.get_member_stats(str(self.guild_id), user.id)
    #
    #     msg = author.mention + "```"
    #     msg += "Current activity stats for " + user.display_name + "\n\n"
    #     msg += "hourly_period\n"
    #     msg += "   start: " + this_stats["activity_stats"]["h_last_check"]["period"] + "\n"
    #     msg += "   credited: " + str(this_stats["activity_stats"]["h_last_check"]["period_credited"]) + "\n"
    #     msg += "   msgs_counted: " + str(this_stats["activity_stats"]["h_last_check"]["msg_count"]) + "\n\n"
    #
    #     msg += "daily_period\n"
    #     msg += "   start: " + this_stats["activity_stats"]["d_last_check"]["period"] + "\n"
    #     msg += "   locked: " + str(this_stats["activity_stats"]["d_last_check"]["period_credited"]) + "\n"
    #     msg += "   payouts_counted: " + str(this_stats["activity_stats"]["d_last_check"]["msg_count"]) + "\n\n"
    #
    #     msg += "weekly_period\n"
    #     msg += "   start: " + this_stats["activity_stats"]["w_last_check"]["period"] + "\n"
    #     msg += "   msgs_counted: " + str(this_stats["activity_stats"]["w_last_check"]["msg_count"]) + "\n"
    #     msg += "```"
    #
    #     await ctx.send(msg)
