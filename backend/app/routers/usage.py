from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models import User
from app.schemas import UsageOut

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageOut)
def get_usage(current_user: User = Depends(get_current_user)) -> UsageOut:
    return UsageOut(
        message_count=current_user.message_count,
        estimated_tokens=current_user.estimated_tokens,
    )
