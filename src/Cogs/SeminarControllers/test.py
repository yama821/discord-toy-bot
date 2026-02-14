import discord
from discord.ext import commands
from discord.commands import slash_command

import config


class Test(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.guild_only()
    @slash_command(
        name="test",
        description="テスト用コマンドです。",
        guild_ids=[config.guild_id],
    )
    async def test(
        self,
        ctx: discord.ApplicationContext,
        command_name: discord.Option(
            input_type=str, description="[省略可]これは引数です",required=False
        ), # type: ignore
    ):
        # ?
        assert isinstance(ctx.guild, discord.Guild)

        await ctx.respond(content="test test test")
        

def setup(bot: discord.Bot):
    bot.add_cog(Test(bot))
