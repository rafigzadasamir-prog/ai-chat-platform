"""Conversation, message (with SSE streaming) and document endpoints."""

from __future__ import annotations

import json
from collections.abc import Generator

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_current_user
from app.llm.base import ChatMessage
from app.llm.factory import get_llm_backend
from app.models import Conversation, DocumentChunk, Message, User
from app.rag import index_document, retrieve_context
from app.schemas import ConversationCreate, ConversationOut, DocumentOut, MessageCreate, MessageOut
from app.usage import record_message_usage

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _get_owned_conversation(db: Session, conversation_id: int, user: User) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        # 404 (not 403) for both "doesn't exist" and "not yours" so we never
        # leak which conversation ids belong to someone else.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = Conversation(user_id=current_user.id, title=payload.title or "New conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Message]:
    conversation = _get_owned_conversation(db, conversation_id, current_user)
    return conversation.messages


@router.post(
    "/{conversation_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    conversation_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    conversation = _get_owned_conversation(db, conversation_id, current_user)
    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only UTF-8 text documents are supported",
        ) from exc

    document_name = file.filename or "document.txt"
    chunk_count = index_document(db, conversation.id, document_name, text)
    if chunk_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is empty")
    return DocumentOut(document_name=document_name, chunk_count=chunk_count)


@router.get("/{conversation_id}/documents", response_model=list[DocumentOut])
def list_documents(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    conversation = _get_owned_conversation(db, conversation_id, current_user)
    rows = (
        db.query(DocumentChunk).filter(DocumentChunk.conversation_id == conversation.id).all()
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.document_name] = counts.get(row.document_name, 0) + 1
    return [DocumentOut(document_name=name, chunk_count=count) for name, count in counts.items()]


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # Snapshot history *before* persisting the new user message, so it's
    # passed separately to the LLM backend rather than duplicated.
    history: list[ChatMessage] = [
        {"role": message.role, "content": message.content} for message in conversation.messages
    ]

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.content)
    db.add(user_message)
    db.commit()

    context_chunks = retrieve_context(db, conversation.id, payload.content)
    llm_backend = get_llm_backend()
    user_text = payload.content
    conversation_id_value = conversation.id
    user_id = current_user.id

    def event_stream() -> Generator[str, None, None]:
        session = SessionLocal()
        try:
            pieces: list[str] = []
            for piece in llm_backend.stream_chat(
                history=history, user_message=user_text, context_chunks=context_chunks
            ):
                pieces.append(piece)
                yield f"data: {json.dumps({'chunk': piece})}\n\n"

            full_text = "".join(pieces)
            assistant_message = Message(
                conversation_id=conversation_id_value, role="assistant", content=full_text
            )
            session.add(assistant_message)
            session.commit()
            session.refresh(assistant_message)

            user = session.get(User, user_id)
            if user is not None:
                record_message_usage(session, user, user_text, full_text)

            yield f"event: done\ndata: {json.dumps({'message_id': assistant_message.id})}\n\n"
        except Exception as exc:  # pragma: no cover - defensive stream-level guard
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
        finally:
            session.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
