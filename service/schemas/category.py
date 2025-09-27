from typing import Optional
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    path: str

    class Config:
        from_attributes = True

