from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def get_current_user(
    x_user: Annotated[str, Header(alias="X-User")],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = db.scalar(
        select(User).where(User.username == x_user)
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Unknown user",
        )

    return user