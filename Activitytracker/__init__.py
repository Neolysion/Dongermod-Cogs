from .activitytracker import ActivityTracker


def setup(bot):
    n = ActivityTracker(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_ready, "on_AA_ready")
    bot.dispatch("AA_ready")
    bot.add_listener(n.activity_listener, "on_message")
