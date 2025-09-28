from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price_at_moment: float
    amount: float


class OrderCreate(BaseModel):
    client_id: int

class OrderResponse(BaseModel):
    id: int 
    client_id: int
    status: str 
    created_at: datetime
    items: List[OrderItemResponse] = [] 
    total_amount: float = 0.0 

    class Config:
        from_attributes = True
