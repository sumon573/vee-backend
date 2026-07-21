"""
Direct Messaging API routes — Phase 9.

Endpoints:
    POST /api/v1/messages/conversations          — start or get a conversation
    GET  /api/v1/messages/conversations          — list own conversations
    GET  /api/v1/messages/{conversation_id}      — list messages in a conversation
    POST /api/v1/messages/{conversation_id}      — send a message

Route ordering note:
    Static paths (/conversations) are defined before dynamic paths
    (/{conversation_id}) so FastAPI does not capture "conversations" as a UUID.

All endpoints require Firebase authentication (get_current_user dependency).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.message import (
    ConversationCreate,
    ConversationListResponse,
    ConversationRead,
    MessageCreate,
    MessageListResponse,
    MessageRead,
)
from app.services.auth import get_current_user
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["Direct Messaging"])


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=200,
    summary="Start or retrieve a conversation",
    description=(
        "Returns the existing one-to-one conversation with the specified user, "
        "or creates one if it does not yet exist. "
        "Blocked users and inactive accounts are rejected."
    ),
)
async def get_or_create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    service = MessageService(db)
    return await service.get_or_create_conversation(
        current_user=current_user,
        recipient_username=body.recipient_username,
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    status_code=200,
    summary="List own conversations",
    description="Returns all conversations the authenticated user participates in, newest first.",
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    service = MessageService(db)
    return await service.list_conversations(current_user=current_user)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


@router.get(
    "/{conversation_id}",
    response_model=MessageListResponse,
    status_code=200,
    summary="List messages in a conversation",
    description=(
        "Returns paginated messages in the specified conversation (newest first). "
        "The requesting user must be a participant."
    ),
)
async def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100, description="Number of messages to return."),
    offset: int = Query(default=0, ge=0, description="Number of messages to skip."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    service = MessageService(db)
    return await service.list_messages(
        current_user=current_user,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{conversation_id}",
    response_model=MessageRead,
    status_code=201,
    summary="Send a message",
    description=(
        "Send a text message in an existing conversation. "
        "The requesting user must be a participant. "
        "Blocked or inactive recipients are rejected."
    ),
)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    service = MessageService(db)
    return await service.send_message(
        current_user=current_user,
        conversation_id=conversation_id,
        body=body,
    )
