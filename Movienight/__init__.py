from .movienight import Movienight


def setup(bot):
    n = Movienight(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_ready, "on_ready")
