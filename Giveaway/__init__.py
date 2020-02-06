from .giveaway import Giveaway
from .dao import DAO


def setup(bot):
    n = Giveaway(bot, DAO())
    bot.add_cog(n)
    bot.add_listener(n.on_ready, "on_ready")
