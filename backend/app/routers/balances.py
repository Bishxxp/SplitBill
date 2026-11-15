from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.balances import GroupBalancesResponse
from app.services.balances import calculate_group_balances

router = APIRouter(
    prefix="/groups",
    tags=["Balances"],
)


@router.get(
    "/{group_id}/balances",
    response_model=GroupBalancesResponse,
)
def get_balances(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return calculate_group_balances(
        db=db,
        group_id=group_id,
        current_user=user,
    )
