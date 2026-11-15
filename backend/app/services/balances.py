from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.expenses import (
    get_total_paid_by_members,
    get_total_shares_by_members,
)
from app.repositories.groups import (
    get_group_by_id,
    get_group_members,
    is_group_member,
)
from app.schemas.balances import (
    GroupBalancesResponse,
    MemberBalance,
)


def calculate_group_balances(
    db: Session,
    group_id: int,
    current_user: User,
) -> GroupBalancesResponse:

    # 1. Check group existence
    group = get_group_by_id(db, group_id)

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    # 2. Check membership
    if not is_group_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not a member of this group",
        )

    # 3. Get group members
    members = get_group_members(db, group_id)

    # 4. Get paid and share totals
    paid_totals = get_total_paid_by_members(db, group_id)
    share_totals = get_total_shares_by_members(db, group_id)

    # 5. Calculate each member's balance
    balances = []

    for user_id, username in members:
        total_paid = paid_totals.get(user_id, Decimal("0.00"))

        total_share = share_totals.get(user_id, Decimal("0.00"))

        balance = total_paid - total_share

        balances.append(
            MemberBalance(
                username=username,
                balance=f"{balance:.2f}",
            )
        )

    # 6. Verify zero-sum balance
    total_balance = sum(
        (Decimal(item.balance) for item in balances),
        Decimal("0.00"),
    )

    if total_balance != Decimal("0.00"):
        raise RuntimeError("Group balances do not sum to zero")

    return GroupBalancesResponse(
        group_id=group_id,
        balances=balances,
    )
