from .activitytracker import ActivityTracker
from .dao import DAO


def setup(bot):
    n = ActivityTracker(bot, DAO())
    bot.add_cog(n)
    bot.add_listener(n.activity_listener, "on_message")
