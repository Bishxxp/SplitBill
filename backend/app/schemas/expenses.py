from typing import Annotated, Literal

from pydantic import BaseModel, Field


class EqualSplit(BaseModel):
    type: Literal["equal"]
    members: list[str]


class ExactSplit(BaseModel):
    type: Literal["exact"]
    shares: dict[str, str]


class ExpenseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    paid_by: str
    amount: str

    split: Annotated[
        EqualSplit | ExactSplit,
        Field(discriminator="type"),
    ]