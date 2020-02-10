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


class Inhouse(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.guild = None
        self.role_mod = None
        self.role_mega = None
        self.role_inhouse = None
        self.role_gold = None

        self.config = Config.get_conf(self, identifier=1834095873645082, force_registration=True)
        default_global = {
            "guild_id": 111772771016515584,
            "mod_role_id": 117296318052958214,
            "mega_role_id": 308667119963209749,
            "inhouse_id": 676393502090854412,
            "gold_id": 676393693640392704,
            "giveaway_path": "data/giveaway.json",
        }
        self.config.register_global(**default_global)

        self.ready = False

    async def on_ready(self):
        self.guild = self.bot.get_guild(await self.config.guild_id())
        self.role_mod = self.guild.get_role(await self.config.mod_role_id())
        self.role_mega = self.guild.get_role(await self.config.mega_role_id())
        self.role_inhouse = self.guild.get_role(await self.config.inhouse_id())
        self.role_gold = self.guild.get_role(await self.config.gold_id())
        self.ready = True

    @commands.guild_only()
    @commands.group(name="inhouse", autohelp=True)
    async def inhouse(self, ctx: commands.Context):
        """
        Use !inhouse join or !inhouse leave
        """
        pass

    @inhouse.command(name="join")
    async def _join(self, ctx):
        if self.role_inhouse not in ctx.author.roles:
            await ctx.author.add_roles(self.role_inhouse)
            await ctx.send(ctx.author.mention + " Joined the in-house league.")
        else:
            await ctx.send(ctx.author.mention + " You are already inhouse.")

    @inhouse.command(name="leave")
    async def _leave(self, ctx: commands.Context):
        if self.role_inhouse in ctx.author.roles:
            await ctx.author.remove_roles(self.role_inhouse)
            await ctx.send(ctx.author.mention + " Left the in-house league.")
        else:
            await ctx.send(ctx.author.mention + " You already left inhouse.")

    @checks.mod()
    @inhouse.command(name="role")
    async def _role(self, ctx: commands.Context, member: discord.Member = None):
        if member:
            if self.role_inhouse in member.roles:
                await ctx.author.remove_roles(self.role_inhouse, reason="Role removed by " + ctx.author.display_name)
                await ctx.send("Inhouse role added to " + member.mention)
            else:
                await ctx.author.add_roles(self.role_inhouse, reason="Role added by " + ctx.author.display_name)
                await ctx.send("Inhouse role removed from " + member.mention)
        else:
            await ctx.send("No member recognized")

    @checks.mod()
    @inhouse.command(name="goldrole")
    async def _goldrole(self, ctx: commands.Context, member: discord.Member = None):
        if member:
            if self.role_gold in member.roles:
                await ctx.author.remove_roles(self.role_gold, reason="Role removed by " + ctx.author.display_name)
                await ctx.send("Gold role added to " + member.mention)
            else:
                await ctx.author.add_roles(self.role_gold, reason="Role added by " + ctx.author.display_name)
                await ctx.send("Gold role removed from " + member.mention)
        else:
            await ctx.send("No member recognized")

    @checks.mod()
    @inhouse.command(name="ping")
    async def _ping(self, ctx: commands.Context):
        await ctx.send(self.role_inhouse.mention)
