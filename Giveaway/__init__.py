from .giveaway import Giveaway
from .dao import DAO

def setup(bot):
    bot.add_cog(Giveaway(bot, DAO()))
