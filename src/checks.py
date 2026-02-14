# src/checks.py
import discord
from discord.ext import commands
from database import async_session
from model import Guild
from sqlalchemy import select

def is_engineer():
    """コマンド実行者がDBに登録された「技術部ロール」を持っているか判定するデコレーター"""
    async def predicate(ctx: discord.ApplicationContext):
        async with async_session() as session:
            stmt = select(Guild).where(Guild.guild_id == ctx.guild.id)
            guild = (await session.execute(stmt)).scalar_one_or_none()

        # 設定されていない場合
        if not guild or not guild.engineer_role_id:
            raise commands.CheckFailure("技術部ロールが未設定です。サーバー管理者に `/setting` で設定を依頼してください。")

        # 実行者が指定されたロールを持っているか確認
        role = ctx.guild.get_role(guild.engineer_role_id)
        if role in ctx.author.roles:
            return True # 実行許可！
        else:
            raise commands.CheckFailure("❌ このコマンドは「技術部」専用です。")
            
    return commands.check(predicate)
