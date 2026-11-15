from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Group, GroupMember, User


def get_groups_by_user(
    db: Session,
    user_id: int,
) -> list[Group]:

    statement = (
        select(Group)
        .join(
            GroupMember,
            Group.id == GroupMember.group_id,
        )
        .where(GroupMember.user_id == user_id)
        .order_by(Group.id)
    )

    return list(db.scalars(statement).all())


def get_group_by_id(
    db: Session,
    group_id: int,
) -> Group | None:
    return db.get(Group, group_id)


def is_group_member(
    db: Session,
    group_id: int,
    user_id: int,
) -> bool:
    membership = db.get(
        GroupMember,
        (group_id, user_id),
    )

    return membership is not None


def get_group_member_names(
    db: Session,
    group_id: int,
) -> list[str]:
    statement = (
        select(User.username)
        .join(
            GroupMember,
            User.id == GroupMember.user_id,
        )
        .where(GroupMember.group_id == group_id)
        .order_by(User.id)
    )

    return list(db.scalars(statement).all())


def get_group_members(
    db: Session,
    group_id: int,
) -> list[tuple[int, str]]:

    statement = (
        select(User.id, User.username)
        .join(
            GroupMember,
            User.id == GroupMember.user_id,
        )
        .where(GroupMember.group_id == group_id)
        .order_by(User.id)
    )

    return [(user_id, username) for user_id, username in db.execute(statement).all()]
