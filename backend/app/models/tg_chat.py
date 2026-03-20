"""Telegram chat / message models for the admin conversation UI."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class TgChat(Base):
    """Represents a Telegram user who has sent at least one message."""

    __tablename__ = "tg_chats"

    id          = Column(Integer, primary_key=True, index=True)
    org_id      = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    tg_user_id  = Column(String(64), nullable=False, index=True)
    tg_username = Column(String(255), nullable=True)
    full_name   = Column(String(255), nullable=True)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    messages = relationship("TgMessage", back_populates="chat", order_by="TgMessage.created_at")


class TgMessage(Base):
    """A single message in a Telegram conversation."""

    __tablename__ = "tg_messages"

    id         = Column(Integer, primary_key=True, index=True)
    chat_id    = Column(Integer, ForeignKey("tg_chats.id"), nullable=False, index=True)
    direction  = Column(String(10), nullable=False)   # 'in' | 'out'
    text       = Column(Text, nullable=False)
    is_read    = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat = relationship("TgChat", back_populates="messages")
