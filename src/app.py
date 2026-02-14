import os
import asyncio

import discord
import database


if __name__ == "__main__":
    # If you don't know what intent is, visit https://docs.pycord.dev/en/stable/intents.html
    intents: discord.Intents = discord.Intents.all()
    intents.typing = False  # Don't react to user's typing event
    intents.presences = False  # Don't react to change of each user's presence

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = discord.Bot(
        intents=intents, 
        description="test bot.",
        loop=loop,
    )

    bot.load_extension("Cogs.seminar_controllers")
    bot.load_extension("Cogs.guild_controllers")

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
