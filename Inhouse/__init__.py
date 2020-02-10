from .inhouse import Inhouse


def setup(bot):
    n = Inhouse(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_ready, "on_ready")
