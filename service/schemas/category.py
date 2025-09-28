from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    """Схема для создания новой категории."""
    name: str
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    """Схема для обновления категории (например, перемещения или переименования)."""
    name: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    """Базовая схема для ответа API по категории."""
    id: int
    name: str
    path: str # Ltree path
    parent_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class CategoryTreeNode(CategoryResponse):
    """Рекурсивная модель для отображения полного дерева категорий.""" # Рекурсивная модель для фронтенда
    children: List[CategoryTreeNode] = []