from pydantic import BaseModel


class InventoryCreate(BaseModel):
    product_id: int
    stock: int

class InventoryResponse(BaseModel):
    product_id: int
    stock: int

    class Config:
        from_attributes = True
