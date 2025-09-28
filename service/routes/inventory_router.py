
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from psycopg2.extensions import connection as Connection
from psycopg2 import errors

from db.session import get_db_connection
from schemas.inventory import InventoryResponse, StockSet, StockAdjust

inventory_router = APIRouter()

@inventory_router.get("/", response_model=List[InventoryResponse])
def list_inventory(skip: int = 0, limit: int = 100, conn: Connection = Depends(get_db_connection)):
    """Получает список всех остатков на складе."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT product_id, stock FROM inventory ORDER BY product_id OFFSET %s LIMIT %s", (skip, limit))
        rows = cursor.fetchall()
        return [InventoryResponse(product_id=row[0], stock=row[1]) for row in rows]

@inventory_router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory_for_product(product_id: int, conn: Connection = Depends(get_db_connection)):
    """Получает остаток для конкретного товара."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT product_id, stock FROM inventory WHERE product_id = %s", (product_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Inventory record not found for this product")
        return InventoryResponse(product_id=row[0], stock=row[1])

@inventory_router.put("/{product_id}", response_model=InventoryResponse)
def set_stock_level(product_id: int, stock_in: StockSet, conn: Connection = Depends(get_db_connection)):
    """
    Устанавливает абсолютное значение остатка.
    Используется для инвентаризации или ручной коррекции.
    """
    with conn.cursor() as cursor:
        # Используем INSERT ... ON CONFLICT (UPSERT), чтобы создать запись, если ее нет.
        # Это делает эндпоинт более надежным.
        cursor.execute(
            """
            INSERT INTO inventory (product_id, stock)
            VALUES (%s, %s)
            ON CONFLICT (product_id) DO UPDATE
            SET stock = EXCLUDED.stock
            RETURNING product_id, stock;
            """,
            (product_id, stock_in.stock)
        )
        row = cursor.fetchone()
        if not row:
             raise HTTPException(status_code=404, detail="Product not found to update inventory for")
        return InventoryResponse(product_id=row[0], stock=row[1])

@inventory_router.patch("/{product_id}/adjust", response_model=InventoryResponse)
def adjust_stock_level(product_id: int, stock_in: StockAdjust, conn: Connection = Depends(get_db_connection)):
    """
    Изменяет (корректирует) остаток на заданное значение.
    Например, поступление товара (change_by: 50) или списание (change_by: -5).
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                UPDATE inventory
                SET stock = stock + %s
                WHERE product_id = %s
                RETURNING product_id, stock;
                """,
                (stock_in.change_by, product_id)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Inventory record not found for this product")
            return InventoryResponse(product_id=row[0], stock=row[1])
        except errors.CheckViolation:
            raise HTTPException(status_code=400, detail="Stock level cannot be negative.")