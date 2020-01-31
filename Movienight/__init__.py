from .movienight import Movienight

def setup(bot):
    n = Movienight(bot)
    bot.add_cog(n)
