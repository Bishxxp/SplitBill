from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Expense, ExpenseShare, User
from app.schemas.expenses import ExpenseCreate


def save_expense(
    db: Session,
    group_id: int,
    data: ExpenseCreate,
    shares: dict[str, Decimal],
    idempotency_key: str,
) -> tuple[Expense, bool]:

    # 1. Find user IDs
    usernames = set(shares) | {data.paid_by}

    users = db.scalars(
        select(User).where(User.username.in_(usernames))
    ).all()

    user_ids = {
        user.username: user.id
        for user in users
    }

    if len(user_ids) != len(usernames):
        raise ValueError("One or more users were not found")

    # 2. Insert expense without duplicating idempotency key
    statement = (
        insert(Expense)
        .values(
            group_id=group_id,
            paid_by_user_id=user_ids[data.paid_by],
            description=data.description,
            amount=Decimal(data.amount),
            idempotency_key=idempotency_key,
        )
        .on_conflict_do_nothing(
            constraint="uq_expenses_group_idempotency"
        )
        .returning(Expense.id)
    )

    expense_id = db.scalar(statement)

    # 3. Existing expense with the same key
    if expense_id is None:
        existing = db.scalar(
            select(Expense).where(
                Expense.group_id == group_id,
                Expense.idempotency_key == idempotency_key,
            )
        )

        if existing is None:
            raise RuntimeError("Could not retrieve existing expense")

        return existing, False

    # 4. Insert shares
    db.add_all([
        ExpenseShare(
            expense_id=expense_id,
            user_id=user_ids[member],
            amount=amount,
        )
        for member, amount in shares.items()
    ])

    db.flush()

    return db.get(Expense, expense_id), True

def get_expense_by_key(
    db: Session,
    group_id: int,
    idempotency_key: str,
) -> Expense | None:
    return db.scalar(
        select(Expense).where(
            Expense.group_id == group_id,
            Expense.idempotency_key == idempotency_key,
        )
    )
    
def get_expense_shares(
    db: Session,
    expense_id: int,
) -> dict[str, Decimal]:
    statement = (
        select(User.username, ExpenseShare.amount)
        .join(
            ExpenseShare,
            User.id == ExpenseShare.user_id,
        )
        .where(ExpenseShare.expense_id == expense_id)
        .order_by(User.id)
    )

    rows = db.execute(statement).all()

    return {
        username: amount
        for username, amount in rows
    }
    
def list_group_expenses(
    db: Session,
    group_id: int,
) -> list[Expense]:

    statement = (
        select(Expense)
        .where(
            Expense.group_id == group_id,
            Expense.is_deleted.is_(False),
        )
        .order_by(
            Expense.created_at.desc(),
            Expense.id.desc(),
        )
    )

    return list(db.scalars(statement).all())

def get_expense_by_id(
    db: Session,
    group_id: int,
    expense_id: int,
) -> Expense | None:

    return db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.group_id == group_id,
            Expense.is_deleted.is_(False),
        )
    )
    
def get_total_paid_by_members(
    db: Session,
    group_id: int,
) -> dict[int, Decimal]:

    statement = (
        select(
            Expense.paid_by_user_id,
            func.sum(Expense.amount),
        )
        .where(
            Expense.group_id == group_id,
            Expense.is_deleted.is_(False),
        )
        .group_by(Expense.paid_by_user_id)
    )

    return {
        user_id: total
        for user_id, total in db.execute(statement).all()
    }

def get_total_shares_by_members(
    db: Session,
    group_id: int,
) -> dict[int, Decimal]:

    statement = (
        select(
            ExpenseShare.user_id,
            func.sum(ExpenseShare.amount),
        )
        .join(
            Expense,
            Expense.id == ExpenseShare.expense_id,
        )
        .where(
            Expense.group_id == group_id,
            Expense.is_deleted.is_(False),
        )
        .group_by(ExpenseShare.user_id)
    )

    return {
        user_id: total
        for user_id, total in db.execute(statement).all()
    }