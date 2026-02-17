import asyncio
import discord
from database import async_session
from model import Guild, Category, SeminarState
from sqlalchemy import select

# ---------------------------------------------------------
# 1. 現在のDBから「設定ダッシュボード」の画面(Embed)を作る関数
# ---------------------------------------------------------
async def get_settings_embed(guild_id: int, guild_name: str, bot: discord.Bot) -> discord.Embed:
    async with async_session() as session:
        stmt_guild = select(Guild).where(Guild.guild_id == guild_id)
        guild = (await session.execute(stmt_guild)).scalar_one_or_none()

        stmt_cat = select(Category).where(Category.guild_id == guild_id)
        categories = (await session.execute(stmt_cat)).scalars().all()

    # 基本設定の表示文字列作成
    role_channel_mention = f"<#{guild.role_setting_channel_id}>" if guild and guild.role_setting_channel_id else "未設定"
    
    # ▼ 追加: システムチャンネルの表示
    system_channel_mention = f"<#{guild.system_channel_id}>" if guild and hasattr(guild, 'system_channel_id') and guild.system_channel_id else "未設定"
    
    engineer_role_mention = f"<@&{guild.engineer_role_id}>" if guild and guild.engineer_role_id else "未設定"
    
    emoji_display = "未設定"
    if guild and guild.interesting_emoji_id:
        emoji_obj = bot.get_emoji(guild.interesting_emoji_id)
        emoji_display = str(emoji_obj) if emoji_obj else f"ID: `{guild.interesting_emoji_id}` (見つかりません)"

    pending_cats = [f"`{category.name}`" for category in categories if category.state == SeminarState.PENDING]
    ongoing_cats = [f"`{category.name}`" for category in categories if category.state == SeminarState.ONGOING]
    paused_cats  = [f"`{category.name}`" for category in categories if category.state == SeminarState.PAUSED]
    finished_cats = [f"`{category.name}`" for category in categories if category.state == SeminarState.FINISHED]

    embed = discord.Embed(
        title="⚙️ サーバー設定ダッシュボード",
        description="現在の設定状況です。下のボタンから変更を行ってください。",
        color=discord.Colour.blue()
    )
    # ▼ 追加: システムチャンネルをEmbedに表示
    embed.add_field(name="現在のシステムチャンネル", value=system_channel_mention, inline=False)
    embed.add_field(name="現在の権限設定チャンネル", value=role_channel_mention, inline=False)
    embed.add_field(name="現在の技術部ロール", value=engineer_role_mention, inline=False)
    embed.add_field(name="現在の興味あり絵文字", value=emoji_display, inline=False)

    embed.add_field(name="🟡 仮立て (PENDING)", value=" ".join(pending_cats) or "登録なし", inline=False)
    embed.add_field(name="🟢 本運用 (ONGOING)", value=" ".join(ongoing_cats) or "登録なし", inline=False)
    embed.add_field(name="🔵 休止中 (PAUSED)", value=" ".join(paused_cats) or "登録なし", inline=False)
    embed.add_field(name="🔴 終了 (FINISHED)", value=" ".join(finished_cats) or "登録なし", inline=False)
    
    return embed

# ---------------------------------------------------------
# ▼ カテゴリー設定用の2段階UI (変更なしのため省略せずにそのまま記述)
# ---------------------------------------------------------
class CategoryStateSelectView(discord.ui.View):
    def __init__(self, bot: discord.Bot, dashboard_message: discord.Message, selected_category: discord.abc.GuildChannel):
        super().__init__(timeout=120)
        self.bot = bot
        self.dashboard_message = dashboard_message
        self.selected_category = selected_category

    @discord.ui.select(
        select_type=discord.ComponentType.string_select,
        placeholder="このカテゴリーの役割を選択してください...",
        options=[
            discord.SelectOption(label="仮立て用", value="PENDING", emoji="🟡"),
            discord.SelectOption(label="本運用用", value="ONGOING", emoji="🟢"),
            discord.SelectOption(label="休止中用", value="PAUSED", emoji="🔵"),
            discord.SelectOption(label="終了済み用", value="FINISHED", emoji="🔴"),
            discord.SelectOption(label="登録を解除する", value="REMOVE", description="Botの管理対象から外します", emoji="🗑️")
        ]
    )
    async def select_state(self, select_menu: discord.ui.Select, interaction: discord.Interaction):
        state_val = select_menu.values[0]
        async with async_session() as session:
            async with session.begin():
                stmt_guild = select(Guild).where(Guild.guild_id == interaction.guild.id)
                guild = (await session.execute(stmt_guild)).scalar_one_or_none()
                if not guild:
                    guild = Guild(guild_id=interaction.guild.id, name=interaction.guild.name)
                    session.add(guild)

                stmt_cat = select(Category).where(Category.category_id == self.selected_category.id)
                category_record = (await session.execute(stmt_cat)).scalar_one_or_none()

                if state_val == "REMOVE":
                    if category_record:
                        await session.delete(category_record)
                        msg = f"🗑️ カテゴリー {self.selected_category.mention} の登録を解除しました。"
                    else:
                        msg = "⚠️ そのカテゴリーは元々登録されていません。"
                else:
                    state_enum = getattr(SeminarState, state_val)
                    if category_record:
                        category_record.state = state_enum
                    else:
                        category_record = Category(
                            category_id=self.selected_category.id,
                            name=self.selected_category.name,
                            guild_id=interaction.guild.id,
                            state=state_enum,
                            category_type="regular"
                        )
                        session.add(category_record)
                    msg = f"✅ カテゴリー {self.selected_category.mention} を `{state_val}` として登録しました！"

        new_embed = await get_settings_embed(interaction.guild.id, interaction.guild.name, self.bot)
        await self.dashboard_message.edit(embed=new_embed)
        await interaction.response.edit_message(content=msg, view=None)

class CategorySelectView(discord.ui.View):
    def __init__(self, bot: discord.Bot, dashboard_message: discord.Message):
        super().__init__(timeout=120)
        self.bot = bot
        self.dashboard_message = dashboard_message

    @discord.ui.select(
        select_type=discord.ComponentType.channel_select,
        placeholder="設定したいカテゴリーを選択...",
        channel_types=[discord.ChannelType.category] 
    )
    async def select_category(self, select_menu: discord.ui.Select, interaction: discord.Interaction):
        selected_category = select_menu.values[0]
        next_view = CategoryStateSelectView(self.bot, self.dashboard_message, selected_category)
        await interaction.response.edit_message(
            content=f"次に、カテゴリー {selected_category.mention} の役割を選択してください：", 
            view=next_view
        )

# ---------------------------------------------------------
# ▼ 修正: ChannelSelectView を役割・システム兼用にする
# ---------------------------------------------------------
class ChannelSelectView(discord.ui.View):
    # setting_type 引数を追加して、どちらの設定か判別できるようにする
    def __init__(self, bot: discord.Bot, dashboard_message: discord.Message, setting_type: str):
        super().__init__(timeout=120)
        self.bot = bot
        self.dashboard_message = dashboard_message
        self.setting_type = setting_type 

    @discord.ui.select(
        select_type=discord.ComponentType.channel_select,
        placeholder="新しいチャンネルを選択...",
        channel_types=[discord.ChannelType.text]
    )
    async def select_callback(self, select_menu: discord.ui.Select, interaction: discord.Interaction):
        selected_channel = select_menu.values[0]
        async with async_session() as session:
            async with session.begin():
                stmt = select(Guild).where(Guild.guild_id == interaction.guild.id)
                guild = (await session.execute(stmt)).scalar_one_or_none()
                if not guild:
                    guild = Guild(guild_id=interaction.guild.id, name=interaction.guild.name)
                    session.add(guild)
                
                # setting_type に応じて保存先カラムを変える
                if self.setting_type == "role":
                    guild.role_setting_channel_id = selected_channel.id
                    target_name = "権限設定チャンネル"
                elif self.setting_type == "system":
                    guild.system_channel_id = selected_channel.id
                    target_name = "システムチャンネル"

        new_embed = await get_settings_embed(interaction.guild.id, interaction.guild.name, self.bot)
        await self.dashboard_message.edit(embed=new_embed)
        await interaction.response.send_message(f"✅ {target_name}を {selected_channel.mention} に変更しました！", ephemeral=True)
        self.stop()

class RoleSelectView(discord.ui.View):
    def __init__(self, bot: discord.Bot, dashboard_message: discord.Message):
        super().__init__(timeout=120)
        self.bot = bot
        self.dashboard_message = dashboard_message

    @discord.ui.select(
        select_type=discord.ComponentType.role_select,
        placeholder="技術部ロールを選択..."
    )
    async def select_callback(self, select_menu: discord.ui.Select, interaction: discord.Interaction):
        selected_role = select_menu.values[0]
        async with async_session() as session:
            async with session.begin():
                stmt = select(Guild).where(Guild.guild_id == interaction.guild.id)
                guild = (await session.execute(stmt)).scalar_one_or_none()
                if not guild:
                    guild = Guild(guild_id=interaction.guild.id, name=interaction.guild.name)
                    session.add(guild)
                guild.engineer_role_id = selected_role.id

        new_embed = await get_settings_embed(interaction.guild.id, interaction.guild.name, self.bot)
        await self.dashboard_message.edit(embed=new_embed)
        await interaction.response.send_message(f"✅ 技術部ロールを {selected_role.mention} に設定しました！", ephemeral=True)
        self.stop()

# ---------------------------------------------------------
# 3. ダッシュボードにくっつくメインのボタン群
# ---------------------------------------------------------
class SettingsDashboardView(discord.ui.View):
    def __init__(self, bot: discord.Bot):
        super().__init__(timeout=180.0) 
        self.bot = bot
        self.message: discord.Message | None = None 

    # ▼ 追加: システムチャンネル用ボタン (row=0)
    @discord.ui.button(label="システムCHの変更", style=discord.ButtonStyle.secondary, row=0)
    async def change_system_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = ChannelSelectView(self.bot, interaction.message, setting_type="system")
        await interaction.response.send_message("変更先のシステムチャンネルを選択してください：", view=view, ephemeral=True)

    # 既存のボタン: 権限設定チャンネル用 (row=0)
    @discord.ui.button(label="権限設定CHの変更", style=discord.ButtonStyle.secondary, row=0)
    async def change_role_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = ChannelSelectView(self.bot, interaction.message, setting_type="role")
        await interaction.response.send_message("変更先の権限設定チャンネルを選択してください：", view=view, ephemeral=True)

    @discord.ui.button(label="技術部ロールの変更", style=discord.ButtonStyle.danger, row=0)
    async def change_engineer_role(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = RoleSelectView(self.bot, interaction.message)
        await interaction.response.send_message("このBotを管理する「技術部」のロールを選択してください：", view=view, ephemeral=True)

    @discord.ui.button(label="カテゴリーの設定", style=discord.ButtonStyle.primary, row=1)
    async def change_category(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = CategorySelectView(self.bot, interaction.message)
        await interaction.response.send_message("設定を変更・登録したいカテゴリーを選択してください：", view=view, ephemeral=True)

    @discord.ui.button(label="興味あり絵文字の変更", style=discord.ButtonStyle.secondary, row=1)
    async def change_emoji(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        prompt_msg = await interaction.channel.send(
            f"{interaction.user.mention} このメッセージに「興味あり」として設定したいスタンプでリアクションしてください！（60秒以内にご対応ください）"
        )
        def check(reaction, user):
            return user == interaction.user and reaction.message.id == prompt_msg.id
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await prompt_msg.edit(content="⏳ タイムアウトしました。もう一度やり直してください。")
            return

        emoji_id = None
        if hasattr(reaction.emoji, "id") and reaction.emoji.id:
            emoji_id = reaction.emoji.id

        if not emoji_id:
            await prompt_msg.edit(content="❌ カスタム絵文字（サーバー独自の絵文字）のみ登録可能です。標準絵文字は使えません。")
            return

        async with async_session() as session:
            async with session.begin():
                stmt = select(Guild).where(Guild.guild_id == interaction.guild.id)
                guild = (await session.execute(stmt)).scalar_one_or_none()
                if not guild:
                    guild = Guild(guild_id=interaction.guild.id, name=interaction.guild.name)
                    session.add(guild)
                guild.interesting_emoji_id = emoji_id

        await prompt_msg.delete()
        new_embed = await get_settings_embed(interaction.guild.id, interaction.guild.name, self.bot)
        await interaction.message.edit(embed=new_embed)
        await interaction.followup.send("✅ 絵文字を更新しました！", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                embed = self.message.embeds[0]
                embed.title = "⚙️ サーバー設定ダッシュボード [操作期限切れ]"
                embed.color = discord.Colour.light_grey()
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass
