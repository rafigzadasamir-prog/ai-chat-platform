from sqlalchemy.orm import Session

from app.models import Conversation, User
from app.rag import chunk_text, index_document, retrieve_context
from app.security import hash_password


def _make_user_and_conversation(db: Session) -> Conversation:
    user = User(email="rag@example.com", hashed_password=hash_password("password123"))
    db.add(user)
    db.commit()
    conversation = Conversation(user_id=user.id, title="RAG test")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def test_chunk_text_returns_single_chunk_for_short_text() -> None:
    assert chunk_text("short text") == ["short text"]


def test_chunk_text_empty_returns_no_chunks() -> None:
    assert chunk_text("   ") == []


def test_chunk_text_splits_long_text_into_multiple_overlapping_chunks() -> None:
    long_text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(long_text, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200


def test_index_document_persists_chunks(db_session: Session) -> None:
    conversation = _make_user_and_conversation(db_session)
    count = index_document(db_session, conversation.id, "notes.txt", "Some short note content.")
    assert count == 1


def test_index_document_empty_text_indexes_nothing(db_session: Session) -> None:
    conversation = _make_user_and_conversation(db_session)
    count = index_document(db_session, conversation.id, "empty.txt", "   ")
    assert count == 0


def test_retrieve_context_returns_empty_without_documents(db_session: Session) -> None:
    conversation = _make_user_and_conversation(db_session)
    assert retrieve_context(db_session, conversation.id, "anything") == []


def test_retrieve_context_ranks_relevant_chunk_first(db_session: Session) -> None:
    conversation = _make_user_and_conversation(db_session)
    index_document(
        db_session,
        conversation.id,
        "mixed.txt",
        "Our return policy allows refunds within thirty days of purchase.",
    )
    index_document(
        db_session,
        conversation.id,
        "mixed.txt",
        "The office is located at 123 Main Street and opens at nine each morning.",
    )

    results = retrieve_context(db_session, conversation.id, "What is your refund policy?")
    assert results
    assert "refunds" in results[0].lower()


def test_retrieve_context_is_scoped_to_its_own_conversation(db_session: Session) -> None:
    conversation_a = _make_user_and_conversation(db_session)
    user_b = User(email="other@example.com", hashed_password=hash_password("password123"))
    db_session.add(user_b)
    db_session.commit()
    conversation_b = Conversation(user_id=user_b.id, title="other")
    db_session.add(conversation_b)
    db_session.commit()
    db_session.refresh(conversation_b)

    index_document(
        db_session, conversation_b.id, "secret.txt", "This belongs to conversation B only."
    )

    assert retrieve_context(db_session, conversation_a.id, "secret") == []
