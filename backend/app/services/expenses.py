from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Expense, User
from app.repositories.expenses import (
    get_expense_by_key,
    get_expense_shares,
    list_group_expenses,
    save_expense,
)
from app.repositories.groups import (
    get_group_by_id,
    get_group_member_names,
    is_group_member,
)
from app.schemas.expenses import EqualSplit, ExpenseCreate, ExpenseResponse
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

def build_expense_response(
    db: Session,
    expense: Expense,
) -> ExpenseResponse:

    payer = db.get(User, expense.paid_by_user_id)

    if payer is None:
        raise RuntimeError("Expense payer not found")

    shares = get_expense_shares(db, expense.id)

    return ExpenseResponse(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        paid_by=payer.username,
        amount=f"{expense.amount:.2f}",
        shares={
            username: f"{amount:.2f}"
            for username, amount in shares.items()
        },
        is_deleted=expense.is_deleted,
        created_at=expense.created_at,
    )


def create_expense(
    db: Session,
    group_id: int,
    current_user: User,
    data: ExpenseCreate,
    idempotency_key: str,
) -> ExpenseResponse:

    # 1. Check group existence
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

    # 3. Return original expense for repeated keys
    existing = get_expense_by_key(
        db,
        group_id,
        idempotency_key,
    )

    if existing is not None:
        return build_expense_response(db, existing)

    # 4. Validate and calculate shares
    shares = validate_expense(
        db,
        group_id,
        current_user,
        data,
    )

    # 5. Save expense and shares atomically
    try:
        expense, _ = save_expense(
            db=db,
            group_id=group_id,
            data=data,
            shares=shares,
            idempotency_key=idempotency_key,
        )

        response = build_expense_response(db, expense)

        db.commit()

        return response

    except Exception:
        db.rollback()
        raise
    
def list_expenses(
    db: Session,
    group_id: int,
    current_user: User,
) -> list[ExpenseResponse]:

    # 1. Check group existence
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

    # 3. Query expenses
    expenses = list_group_expenses(db, group_id)

    # 4. Convert to response schema
    return [
        build_expense_response(db, expense)
        for expense in expenses
    ]