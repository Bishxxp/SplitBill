from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.groups import GroupDetailResponse, GroupResponse
from app.services.groups import get_group_detail, list_user_groups

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
)


@router.get("", response_model=list[GroupResponse])
def get_groups(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return list_user_groups(db, user)


@router.get("/{group_id}", response_model=GroupDetailResponse)
def get_group(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return get_group_detail(db, user, group_id)
