import datetime
import enum
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class SeminarState(enum.Enum):
    PENDING = enum.auto()
    ONGOING = enum.auto()
    PAUSED = enum.auto()
    FINISHED = enum.auto()


class Base(DeclarativeBase, MappedAsDataclass):
    pass


# 1. サーバー (Guild) テーブル
class Guild(Base):
    __tablename__ = "guild"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    guild_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    
    interesting_emoji_id: Mapped[Optional[int]] = mapped_column(default=None)
    role_setting_channel_id: Mapped[Optional[int]] = mapped_column(default=None)
    system_channel_id: Mapped[Optional[int]] = mapped_column(default=None)
    engineer_role_id: Mapped[Optional[int]] = mapped_column(default=None)


# 2. カテゴリ (Category) テーブル
class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    
    guild_id: Mapped[int] = mapped_column(ForeignKey("guild.guild_id"))
    state: Mapped[SeminarState]
    category_type: Mapped[str] = mapped_column(default="regular")


# 3. ゼミ (Seminar) テーブル
class Seminar(Base):
    __tablename__ = "seminar"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    category_id: Mapped[int] = mapped_column(ForeignKey("category.category_id"))
    
    name: Mapped[str]
    created_at: Mapped[datetime.datetime]
    finished_at: Mapped[Optional[datetime.datetime]]
    leader_id: Mapped[int]
    
    channel_id: Mapped[int] = mapped_column(unique=True)
    role_id: Mapped[int] = mapped_column(unique=True)
    role_setting_message_id: Mapped[int] = mapped_column(unique=True)
