from pydantic import BaseModel, ConfigDict


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    
class GroupDetailResponse(GroupResponse):
    members: list[str]