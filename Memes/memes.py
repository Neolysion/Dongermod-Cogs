import time
import asyncio
import random
import logging
from random import randint
from os.path import dirname, abspath
from typing import Optional, Union

import discord

from redbot.cogs.bank import check_global_setting_admin

from redbot.core.bot import Red
from redbot.core import commands, checks, bank, errors, i18n
from redbot.core.utils.mod import get_audit_reason
from redbot.core import Config, modlog

log = logging.getLogger("red.mod")
_ = i18n.Translator("Mod", __file__)
pd = dirname(dirname(abspath(__file__)))


class SetParser:
    def __init__(self, argument):
        allowed = ("+", "-")
        self.sum = int(argument)
        if argument and argument[0] in allowed:
            if self.sum < 0:
                self.operation = "withdraw"
            elif self.sum > 0:
                self.operation = "deposit"
            else:
                raise RuntimeError
            self.sum = abs(self.sum)
        elif argument.isdigit():
            self.operation = "set"
        else:
            raise RuntimeError


class Memes(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=46772245354364, force_registration=True)
        default_global = {
            "cost_dank": 25000,
            "guild_id": 111772771016515584,
            "role_dank_id": 353238417212964865,
            "mod_role_id": 117296318052958214,
            "mega_role_id": 308667119963209749,
            "giveaway_path": "data/giveaway.json",
        }
        self.config.register_global(**default_global)

        self.modpride_running = False
        self.dank_cd = False
        self.races = 0
        self.guild = None
        self.role_dank = None
        self.role_mod = None
        self.role_mega = None
        self.ready = False
        self.ban_queue = []
        self.rainbowcolors = [
            0xFF0000,
            0xFF0F00,
            0xFF1F00,
            0xFF2E00,
            0xFF3D00,
            0xFF4D00,
            0xFF5C00,
            0xFF6B00,
            0xFF7A00,
            0xFF8A00,
            0xFF9900,
            0xFFA800,
            0xFFB800,
            0xFFC700,
            0xFFD600,
            0xFFE500,
            0xFFF500,
            0xFAFF00,
            0xEBFF00,
            0xDBFF00,
            0xCCFF00,
            0xBDFF00,
            0xADFF00,
            0x9EFF00,
            0x8FFF00,
            0x80FF00,
            0x70FF00,
            0x61FF00,
            0x52FF00,
            0x42FF00,
            0x33FF00,
            0x24FF00,
            0x14FF00,
            0x05FF00,
            0x00FF0A,
            0x00FF19,
            0x00FF29,
            0x00FF38,
            0x00FF47,
            0x00FF57,
            0x00FF66,
            0x00FF75,
            0x00FF85,
            0x00FF94,
            0x00FFA3,
            0x00FFB3,
            0x00FFC2,
            0x00FFD1,
            0x00FFE0,
            0x00FFF0,
            0x00FFFF,
            0x00F0FF,
            0x00E0FF,
            0x00D1FF,
            0x00C2FF,
            0x00B2FF,
            0x00A3FF,
            0x0094FF,
            0x0085FF,
            0x0075FF,
            0x0066FF,
            0x0057FF,
            0x0047FF,
            0x0038FF,
            0x0029FF,
            0x0019FF,
            0x000AFF,
            0x0500FF,
            0x1400FF,
            0x2400FF,
            0x3300FF,
            0x4200FF,
            0x5200FF,
            0x6100FF,
            0x7000FF,
            0x8000FF,
            0x8F00FF,
            0x9E00FF,
            0xAD00FF,
            0xBD00FF,
            0xCC00FF,
            0xDB00FF,
            0xEB00FF,
            0xFA00FF,
            0xFF00F5,
            0xFF00E6,
            0xFF00D6,
            0xFF00C7,
            0xFF00B8,
            0xFF00A8,
            0xFF0099,
            0xFF008A,
            0xFF007A,
            0xFF006B,
            0xFF005C,
            0xFF004D,
            0xFF003D,
            0xFF002E,
            0xFF001F,
            0xFF000F,
        ]

    async def on_ready(self):
        self.guild = self.bot.get_guild(await self.config.guild_id())
        self.role_dank = self.guild.get_role(await self.config.role_dank_id())
        self.role_mod = self.guild.get_role(await self.config.mod_role_id())
        self.role_mega = self.guild.get_role(await self.config.mega_role_id())
        self.ready = True

    @commands.group(name="buy", autohelp=True)
    async def buy(self, ctx: commands.Context):
        """
        Buy roles
        """
        pass

    @buy.command(name="dank")
    async def _dank(self, ctx):
        """
        Purchase the Dank Memer role (Cost: 25000)
        """

        if self.role_dank in ctx.author.roles:
            await ctx.send("You already have that role " + ctx.author.mention)
            return True

        currency_name = await bank.get_currency_name(ctx.guild)
        try:
            await bank.withdraw_credits(ctx.author, self.config.cost_dank())
        except ValueError:
            return await ctx.send(
                f"You don't have enough {currency_name} (Cost: {self.config.cost_dank()}) {ctx.author.mention}"
            )
        else:
            await ctx.author.add_roles(self.role_dank)
            await ctx.send(
                "You bought the "
                + self.role_dank.name
                + " role for "
                + str(self.config.cost_dank())
                + " "
                + currency_name
                + " "
                + ctx.author.mention
            )

    @commands.guild_only()
    @checks.mod()
    @commands.command(pass_context=True, no_pm=True)
    async def modpride(self, ctx):
        if not self.modpride_running:
            self.modpride_running = True
            for c in self.rainbowcolors:
                dcol = discord.Colour(c)
                await asyncio.sleep(0.2)
                await self.role_mod.edit(colour=dcol)
            await self.role_mod.edit(colour=discord.Colour(0xE74C3C))
            self.modpride_running = False

    async def dankcolors(self):
        self.dank_cd = True

        def r():
            return random.randint(0, 255)

        dcol = discord.Colour(int("%02X%02X%02X" % (r(), r(), r()), 16))
        await self.role_dank.edit(colour=dcol)
        await asyncio.sleep(300)
        self.dank_cd = False

    @commands.guild_only()
    @commands.command(pass_context=True, no_pm=True)
    async def dank(self, ctx):
        if self.role_dank in ctx.author.roles:
            if not self.dank_cd:
                await self.dankcolors()
            else:
                await ctx.send("Command on cooldown...")

    @commands.command(pass_context=True, no_pm=True)
    async def addme(self, ctx):
        file = discord.File(pd + "/media/addme.png", filename=None, spoiler=False)
        await ctx.send(file=file)

    @commands.command(pass_context=True, no_pm=True)
    async def cialis(self, ctx):
        file = discord.File(pd + "/media/cialis.png", filename=None, spoiler=False)
        await ctx.send(file=file)

    @commands.command(pass_context=True, no_pm=True)
    async def furries(self, ctx):
        file = discord.File(pd + "/media/furries.gif", filename=None, spoiler=False)
        await ctx.send(file=file)

    @commands.command(pass_context=True, no_pm=True)
    async def plebs(self, ctx):
        file = discord.File(pd + "/media/plebs.png", filename=None, spoiler=False)
        await ctx.send(file=file)

    @commands.command(pass_context=True, no_pm=True)
    async def sgbarcon(self, ctx):
        file = discord.File(pd + "/media/sgbarcon.png", filename=None, spoiler=False)
        await ctx.send(file=file)

    @commands.command()
    @commands.guild_only()
    async def addmegarole(
            self, ctx: commands.Context, user: discord.Member, *, reason: str = None
    ):
        """
        """
        author = ctx.author
        if (
                author.id == 147349764281729024
                or author.id == 383195095610163200
                or author.id == 95174017710821376
        ):
            await ctx.message.mentions[0].add_roles(self.role_mega,
                                                    reason="Assigned manually by " + author.display_name + "")
            await ctx.send("Role set")

    @commands.command()
    @commands.guild_only()
    async def removemegarole(
            self, ctx: commands.Context, user: discord.Member, *, reason: str = None
    ):
        """
        """
        author = ctx.author
        if (
                author.id == 147349764281729024
                or author.id == 383195095610163200
                or author.id == 95174017710821376
        ):
            await ctx.message.mentions[0].remove_roles(self.role_mega,
                                                       reason="Removed manually by " + author.display_name + "")
            await ctx.send("Role removed")

    @commands.command(pass_context=True, no_pm=True)
    async def vroom(self, ctx):
        if self.races < 3:
            self.races += 1
            start_time = time.time()
            m = await ctx.send("﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏")
            await asyncio.sleep(0.5)
            await m.edit(content=":wheelchair:﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏")
            for _ in range(19):
                newtick = m.content[:-1]
                newtick = "﹏" + newtick
                await asyncio.sleep((randint(5, 30) / 10))
                await m.edit(content=newtick)
            elapsed_time = time.time() - start_time
            await m.edit(
                content=ctx.message.author.mention
                        + " finished in "
                        + str(round(elapsed_time, 2))
                        + "s"
            )
            self.races -= 1
        else:
            await ctx.send(
                ctx.message.author.mention
                + " there can only be up to 3 races at the same time. Try later..."
            )

    @commands.command(pass_context=True, no_pm=True)
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        """Show the user's account balance.
        Defaults to yours."""
        if user is None:
            user = ctx.author

        bal = await bank.get_balance(user)
        currency = await bank.get_currency_name(ctx.guild)

        await ctx.send(
            "{user}'s balance is {num} {currency}".format(
                user=user.display_name, num=bal, currency=currency
            )
        )

    @check_global_setting_admin()
    @commands.command(pass_context=True, no_pm=True)
    async def balanceset(
            self, ctx: commands.Context, to: discord.Member, creds: SetParser
    ):
        """Set the balance of user's bank account.
        Passing positive and negative values will add/remove currency instead.
        Examples:
        - `[p]bank set @Twentysix 26` - Sets balance to 26
        - `[p]bank set @Twentysix +2` - Increases balance by 2
        - `[p]bank set @Twentysix -6` - Decreases balance by 6
        """
        author = ctx.author
        currency = await bank.get_currency_name(ctx.guild)

        try:
            if creds.operation == "deposit":
                await bank.deposit_credits(to, creds.sum)
                msg = "{author} added {num} {currency} to {user}'s account.".format(
                    author=author.display_name,
                    num=creds.sum,
                    currency=currency,
                    user=to.display_name,
                )
            elif creds.operation == "withdraw":
                await bank.withdraw_credits(to, creds.sum)
                msg = "{author} removed {num} {currency} from {user}'s account.".format(
                    author=author.display_name,
                    num=creds.sum,
                    currency=currency,
                    user=to.display_name,
                )
            else:
                await bank.set_balance(to, creds.sum)
                msg = "{author} set {user}'s account balance to {num} {currency}.".format(
                    author=author.display_name,
                    num=creds.sum,
                    currency=currency,
                    user=to.display_name,
                )
        except (ValueError, errors.BalanceTooHigh) as e:
            await ctx.send(str(e))
        else:
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @checks.admin_or_permissions(kick_members=True)
    async def superkick(
            self, ctx: commands.Context, user: discord.Member, *, reason: str = None
    ):
        """Kick a user.
        If a reason is specified, it will be the reason that shows up
        in the audit log.
        """
        author = ctx.author
        guild = ctx.guild

        if author == user:
            await ctx.send(
                _("I cannot let you do that. Self-harm is bad {emoji}").format(
                    emoji="\N{PENSIVE FACE}"
                )
            )
            return
        elif ctx.guild.me.top_role <= user.top_role or user == ctx.guild.owner:
            await ctx.send(_("I cannot do that due to discord hierarchy rules"))
            return
        audit_reason = get_audit_reason(author, reason)
        try:
            await guild.kick(user, reason=audit_reason)
            log.info(
                "{}({}) kicked {}({})".format(
                    author.name, author.id, user.name, user.id
                )
            )
        except discord.errors.Forbidden:
            await ctx.send(_("I'm not allowed to do that."))
        except Exception as e:
            print(e)
        else:
            try:
                await modlog.create_case(
                    self.bot,
                    guild,
                    ctx.message.created_at,
                    "kick",
                    user,
                    author,
                    reason,
                    until=None,
                    channel=None,
                )
            except RuntimeError as e:
                await ctx.send(e)
            await ctx.send(_("Done. That felt good."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @checks.admin_or_permissions(ban_members=True)
    async def superban(
            self,
            ctx: commands.Context,
            user: discord.Member,
            days: Optional[int] = 0,
            *,
            reason: str = None,
    ):
        """Ban a user from this server and optionally delete days of messages.
        If days is not a number, it's treated as the first word of the reason.
        Minimum 0 days, maximum 7. Defaults to 0."""

        result = await self.ban_user(
            user=user, ctx=ctx, days=days, reason=reason, create_modlog_case=True
        )

        if result is True:
            await ctx.send(_("Done. It was about time."))
        elif isinstance(result, str):
            await ctx.send(result)

    async def ban_user(
            self,
            user: discord.Member,
            ctx: commands.Context,
            days: int = 0,
            reason: str = None,
            create_modlog_case=False,
    ) -> Union[str, bool]:
        author = ctx.author
        guild = ctx.guild

        if author == user:
            return _("I cannot let you do that. Self-harm is bad {}").format(
                "\N{PENSIVE FACE}"
            )
        elif guild.me.top_role <= user.top_role or user == guild.owner:
            return _("I cannot do that due to discord hierarchy rules")
        elif not (0 <= days <= 7):
            return _("Invalid days. Must be between 0 and 7.")

        audit_reason = get_audit_reason(author, reason)

        queue_entry = (guild.id, user.id)
        self.ban_queue.append(queue_entry)
        try:
            await guild.ban(user, reason=audit_reason, delete_message_days=days)
            log.info(
                "{}({}) banned {}({}), deleting {} days worth of messages".format(
                    author.name, author.id, user.name, user.id, str(days)
                )
            )
        except discord.Forbidden:
            self.ban_queue.remove(queue_entry)
            return _("I'm not allowed to do that.")
        except Exception as e:
            self.ban_queue.remove(queue_entry)
            return e  # TODO: impproper return type? Is this intended to be re-raised?

        if create_modlog_case:
            try:
                await modlog.create_case(
                    self.bot,
                    guild,
                    ctx.message.created_at,
                    "ban",
                    user,
                    author,
                    reason,
                    until=None,
                    channel=None,
                )
            except RuntimeError as e:
                return _(
                    "The user was banned but an error occurred when trying to "
                    "create the modlog entry: {reason}"
                ).format(reason=e)

        return True
