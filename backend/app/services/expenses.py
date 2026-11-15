from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.groups import (
    get_group_by_id,
    get_group_member_names,
    is_group_member,
)
from app.schemas.expenses import EqualSplit, ExpenseCreate
from app.services.splitting import split_equal, split_exact


def validate_expense(
    db: Session,
    group_id: int,
    current_user: User,
    data: ExpenseCreate,
) -> dict[str, Decimal]:

    # 1. Check if group exists
    group = get_group_by_id(db, group_id)

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    # 2. Check requester membership
    if not is_group_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not a member of this group",
        )

    # 3. Get all valid members
    group_members = set(get_group_member_names(db, group_id))

    # 4. Validate payer
    if data.paid_by not in group_members:
        raise HTTPException(
            status_code=422,
            detail="Payer must be a member of this group",
        )

    # 5. Identify split members
    if isinstance(data.split, EqualSplit):
        split_members = data.split.members
    else:
        split_members = list(data.split.shares.keys())

    # 6. Validate split membership
    for member in split_members:
        if member not in group_members:
            raise HTTPException(
                status_code=422,
                detail=f"{member} is not a member of this group",
            )

    # 7. Calculate shares
    try:
        if isinstance(data.split, EqualSplit):
            shares = split_equal(
                data.amount,
                data.split.members,
            )
        else:
            shares = split_exact(
                data.amount,
                data.split.shares,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return shares