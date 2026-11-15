from pydantic import BaseModel


class MemberBalance(BaseModel):
    username: str
    balance: str


class GroupBalancesResponse(BaseModel):
    group_id: int
    balances: list[MemberBalance]
