from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: int
    category_id: int

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    category_id: int
    stock: int

    class Config:
        from_attributes = True
