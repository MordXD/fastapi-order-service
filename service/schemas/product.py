from typing import Optional
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: int
    category_id: int
    initial_stock: int = 0

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    category_id: int
    stock: Optional[int] = 0

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: str
    price: float
    category_id: int