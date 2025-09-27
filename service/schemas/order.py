from datetime import datetime
from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    order_id: int
    price_at_moment: float
    amount: float


class OrderCreate(BaseModel):
    client_id: int
    status_order: str = "NEW"

class OrderResponse(BaseModel):
    order_id: int
    client_id: int
    created_at: datetime
    status_order: str

    class Config:
        from_attributes = True
