"""Admin API for Telegram bot conversations."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..core.auth import get_current_active_user_or_demo
from ..core.config import settings
from ..core.database import get_db
from ..models.tg_chat import TgChat, TgMessage
from ..models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

BOT_TOKEN = getattr(settings, "BOT_TOKEN", "")


# ── Schemas ───────────────────────────────────────────────────────────────────

class IncomingMessage(BaseModel):
    """Posted by the Telegram bot when a user sends a message."""
    tg_user_id:  str
    tg_username: Optional[str] = None
    full_name:   Optional[str] = None
    text:        str


class ReplyRequest(BaseModel):
    text: str


class MessageOut(BaseModel):
    id:         int
    direction:  str
    text:       str
    is_read:    bool
    created_at: str

    class Config:
        from_attributes = True


class ChatOut(BaseModel):
    id:          int
    tg_user_id:  str
    tg_username: Optional[str]
    full_name:   Optional[str]
    is_resolved: bool
    unread:      int
    last_text:   Optional[str]
    created_at:  str

    class Config:
        from_attributes = True


# ── Bot webhook endpoint (no auth, called by bot process) ─────────────────────

@router.post("/messages")
async def receive_message(
    payload: IncomingMessage,
    db: AsyncSession = Depends(get_db),
):
    """Called by the Telegram bot to store an incoming user message."""
    # Find or create chat (per org_id=1 for single-org setup;
    # pass org_id header for multi-tenant later)
    result = await db.execute(
        select(TgChat).where(TgChat.tg_user_id == payload.tg_user_id).limit(1)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        chat = TgChat(
            org_id=1,   # TODO: derive from API key / org context
            tg_user_id=payload.tg_user_id,
            tg_username=payload.tg_username,
            full_name=payload.full_name,
        )
        db.add(chat)
        await db.flush()

    msg = TgMessage(chat_id=chat.id, direction="in", text=payload.text)
    db.add(msg)
    await db.commit()
    return {"ok": True, "chat_id": chat.id}


# ── Admin endpoints (require auth) ────────────────────────────────────────────

@router.get("/chats", response_model=List[ChatOut])
async def list_chats(
    resolved: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """List all Telegram conversations for this organisation."""
    query = (
        select(TgChat)
        .options(selectinload(TgChat.messages))
        .where(TgChat.org_id == current_user.org_id)
    )
    if resolved is not None:
        query = query.where(TgChat.is_resolved == resolved)
    query = query.order_by(TgChat.updated_at.desc().nullslast(), TgChat.created_at.desc())

    result = await db.execute(query)
    chats = result.scalars().all()

    out = []
    for chat in chats:
        msgs = chat.messages
        unread = sum(1 for m in msgs if m.direction == "in" and not m.is_read)
        last_text = msgs[-1].text[:80] if msgs else None
        out.append(ChatOut(
            id=chat.id,
            tg_user_id=chat.tg_user_id,
            tg_username=chat.tg_username,
            full_name=chat.full_name,
            is_resolved=chat.is_resolved,
            unread=unread,
            last_text=last_text,
            created_at=str(chat.created_at),
        ))
    return out


@router.get("/chats/{chat_id}/messages", response_model=List[MessageOut])
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Get message history for a chat. Marks incoming messages as read."""
    result = await db.execute(
        select(TgChat)
        .options(selectinload(TgChat.messages))
        .where(TgChat.id == chat_id, TgChat.org_id == current_user.org_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(404, "Chat not found")

    # Mark all incoming as read
    for msg in chat.messages:
        if msg.direction == "in" and not msg.is_read:
            msg.is_read = True
    await db.commit()

    return [
        MessageOut(
            id=m.id,
            direction=m.direction,
            text=m.text,
            is_read=m.is_read,
            created_at=str(m.created_at),
        )
        for m in chat.messages
    ]


@router.post("/chats/{chat_id}/reply")
async def reply_to_chat(
    chat_id: int,
    body: ReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Send a reply to a Telegram user and save it in the conversation history."""
    result = await db.execute(
        select(TgChat).where(TgChat.id == chat_id, TgChat.org_id == current_user.org_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(404, "Chat not found")

    # Deliver via Telegram Bot API
    if BOT_TOKEN:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat.tg_user_id, "text": body.text},
                )
                resp.raise_for_status()
        except Exception as exc:
            logger.error(f"Failed to send Telegram message: {exc}")
            raise HTTPException(502, f"Telegram delivery failed: {exc}")
    else:
        logger.warning("BOT_TOKEN not configured — message not delivered to Telegram")

    # Save outgoing message
    msg = TgMessage(chat_id=chat.id, direction="out", text=body.text, is_read=True)
    db.add(msg)
    await db.commit()
    return {"ok": True}


@router.patch("/chats/{chat_id}/resolve")
async def resolve_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Mark a conversation as resolved."""
    result = await db.execute(
        select(TgChat).where(TgChat.id == chat_id, TgChat.org_id == current_user.org_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(404, "Chat not found")
    chat.is_resolved = True
    await db.commit()
    return {"ok": True}
