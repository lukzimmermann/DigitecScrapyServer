from pydantic import BaseModel

class BatchRequestDto(BaseModel):
    token: str
    ip: str
    display_name: str

    def __repr__(self) -> str:
        return super().__repr__()
    
class SendBatchDto(BaseModel):
    id: str

    def __repr__(self) -> str:
        return super().__repr__()
    
class BatchDto(BaseModel):
    id: str
    user_name: str
    number_list: list[int]
    created: str
    interval: float

class JobStatusDto(BaseModel):
    user_name: str
    created: str
    min_number: int
    max_number: int
    number_count: int
