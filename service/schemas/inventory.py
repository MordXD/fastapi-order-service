from pydantic import BaseModel

class InventoryResponse(BaseModel):
    """Схема для ответа API по остаткам."""
    product_id: int
    stock: int

    class Config:
        from_attributes = True

class StockSet(BaseModel):
    """Схема для установки абсолютного значения остатка (инвентаризация)."""
    stock: int

class StockAdjust(BaseModel):
    """Схема для изменения остатка (поступление/списание)."""
    change_by: int # может - или плюс