from .memes import Memes
# import asyncio


def setup(bot):
    n = Memes(bot)
    # loop = asyncio.get_event_loop()
    # loop.create_task(n.dankcolors())
    bot.add_cog(n)
