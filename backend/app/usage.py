"""Naive SaaS-style usage metering (no real billing integration)."""

from sqlalchemy.orm import Session

from app.models import User


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token, matching common
    rule-of-thumb heuristics for English text without needing a real
    tokenizer dependency."""
    return max(1, len(text) // 4)


def record_message_usage(db: Session, user: User, user_text: str, assistant_text: str) -> None:
    user.message_count += 1
    user.estimated_tokens += estimate_tokens(user_text) + estimate_tokens(assistant_text)
    db.add(user)
    db.commit()
