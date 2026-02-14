import os


import discord


if __name__ == "__main__":
    # If you don't know what intent is, visit https://docs.pycord.dev/en/stable/intents.html
    intents: discord.Intents = discord.Intents.all()
    intents.typing = False  # Don't react to user's typing event
    intents.presences = False  # Don't react to change of each user's presence

    bot = discord.Bot(intents=intents, description="Wathematicaのゼミを管理します。")

    bot.load_extension("Cogs.seminar_controllers")

    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
