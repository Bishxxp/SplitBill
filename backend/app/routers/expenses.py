from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.expenses import ExpenseCreate, ExpenseResponse
from app.services.expenses import create_expense

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