from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Group, User
from app.repositories.groups import (
    get_group_by_id,
    get_group_member_names,
    get_groups_by_user,
    is_group_member,
)
from app.schemas.groups import GroupDetailResponse


def list_user_groups(
    db: Session,
    user: User,
) -> list[Group]:
    return get_groups_by_user(db, user.id)

def get_group_detail(
    db: Session,
    user: User,
    group_id: int,
) -> GroupDetailResponse:

    group = get_group_by_id(db, group_id)

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    if not is_group_member(db, group_id, user.id):
        raise HTTPException(
            status_code=403,
            detail="Not a member of this group",
        )

    members = get_group_member_names(db, group_id)

    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        members=members,
    )