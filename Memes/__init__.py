# import asyncio
from .memes import Memes



def setup(bot):
    n = Memes(bot)
    # loop = asyncio.get_event_loop()
    # loop.create_task(n.dankcolors())
    bot.add_cog(n)
    bot.add_listener(n.on_ready, "on_MEME_ready")
    bot.dispatch("MEME_ready")
