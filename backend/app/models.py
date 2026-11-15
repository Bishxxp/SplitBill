from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )


class Expense(Base):
    __tablename__ = "expenses"

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "idempotency_key",
            name="uq_expenses_group_idempotency"
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_expenses_positive_amount"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"),
        nullable=False
    )

    paid_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_expense_shares_nonnegative"
        ),
    )

    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id"),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )