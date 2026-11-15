from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.expenses import ExpenseCreate, ExpenseResponse
from app.services.expenses import (
    create_expense,
    delete_expense,
    list_expenses,
)

router = APIRouter(
    prefix="/groups/{group_id}/expenses",
    tags=["Expenses"],
)


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=201,
)
def add_expense(
    group_id: int,
    data: ExpenseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key"),
    ],
):
    if not idempotency_key.strip() or len(idempotency_key) > 128:
        raise HTTPException(
            status_code=422,
            detail="Invalid Idempotency-Key",
        )

    return create_expense(
        db=db,
        group_id=group_id,
        current_user=user,
        data=data,
        idempotency_key=idempotency_key,
    )


@router.get(
    "",
    response_model=list[ExpenseResponse],
)
def get_expenses(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return list_expenses(
        db=db,
        group_id=group_id,
        current_user=user,
    )


@router.delete(
    "/{expense_id}",
    status_code=204,
)
def remove_expense(
    group_id: int,
    expense_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    delete_expense(
        db=db,
        group_id=group_id,
        expense_id=expense_id,
        current_user=user,
    )
