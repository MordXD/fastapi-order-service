from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import List
from psycopg2.extensions import connection as Connection, cursor as Cursor

from db.session import get_db_connection

from schemas.order import OrderCreate, OrderItemCreate, OrderResponse, OrderItemResponse

order_router = APIRouter()

def _fetch_order_details(order_id: int, cursor: Cursor) -> OrderResponse | None:
    """Получает все детали заказа из БД и собирает Pydantic модель."""
    cursor.execute(
        "SELECT id, client_id, status, created_at FROM orders WHERE id = %s",
        (order_id,)
    )
    order_row = cursor.fetchone()
    if not order_row:
        return None
    cursor.execute(
        """
        SELECT 
            oi.product_id, 
            p.name as product_name, 
            oi.qty, 
            oi.price_at_moment, 
            oi.amount
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
        ORDER BY p.name
        """,
        (order_id,)
    )
    items_rows = cursor.fetchall()
    order_items = [
        OrderItemResponse(
            product_id=row[0],
            product_name=row[1],
            quantity=row[2],
            price_at_moment=float(row[3]), 
            amount=float(row[4])
        ) for row in items_rows
    ]
    total_amount = sum(item.amount for item in order_items)
    return OrderResponse(
        id=order_row[0],
        client_id=order_row[1],
        status=order_row[2],
        created_at=order_row[3],
        items=order_items,
        total_amount=round(total_amount, 2)
    )

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, conn: Connection = Depends(get_db_connection)):
    """[C]reate: Создает новый пустой заказ для клиента."""
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO orders (client_id) VALUES (%s) RETURNING id",
            (order_in.client_id,)
        )
        new_order_id = cursor.fetchone()[0]
        return _fetch_order_details(new_order_id, cursor)

#Можно изменить на оконную фукнцию, но для простоты и поддежрки оставим так
@order_router.get("/", response_model=List[OrderResponse])
def list_orders(skip: int = 0, limit: int = 20, conn: Connection = Depends(get_db_connection)):
    """[R]ead: Получает список заказов эффективно, избегая проблемы N+1."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, client_id, status, created_at 
            FROM orders 
            ORDER BY created_at DESC 
            OFFSET %s LIMIT %s
            """,
            (skip, limit)
        )
        orders_rows = cursor.fetchall()
        if not orders_rows:
            return []
        order_ids = [row[0] for row in orders_rows]
        cursor.execute(
            """
            SELECT 
                oi.order_id, 
                oi.product_id, 
                p.name as product_name, 
                oi.qty, 
                oi.price_at_moment, 
                oi.amount
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ANY(%s) -- Используем ANY для поиска в массиве ID
            """,
            (order_ids,) 
        )
        items_rows = cursor.fetchall()
        items_by_order_id = {}
        for row in items_rows:
            order_id = row[0]
            if order_id not in items_by_order_id:
                items_by_order_id[order_id] = []
            
            items_by_order_id[order_id].append(
                OrderItemResponse(
                    product_id=row[1],
                    product_name=row[2],
                    quantity=row[3],
                    price_at_moment=float(row[4]),
                    amount=float(row[5])
                )
            )
        result = []
        for order_row in orders_rows:
            order_id = order_row[0]
            order_items = items_by_order_id.get(order_id, [])
            total_amount = sum(item.amount for item in order_items)
            
            result.append(
                OrderResponse(
                    id=order_row[0],
                    client_id=order_row[1],
                    status=order_row[2],
                    created_at=order_row[3],
                    items=order_items,
                    total_amount=round(total_amount, 2)
                )
            )
            
        return result


@order_router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, conn: Connection = Depends(get_db_connection)):
    """[R]ead: Получает полную информацию о конкретном заказе."""
    with conn.cursor() as cursor:
        order = _fetch_order_details(order_id, cursor)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order


@order_router.post("/{order_id}/items", response_model=OrderResponse)
def add_item_to_order(order_id: int, item_in: OrderItemCreate, conn: Connection = Depends(get_db_connection)):
    """[U]pdate: Добавляет товар в заказ (ключевая логика задания)."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM orders WHERE id = %s FOR UPDATE", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")
        cursor.execute(
            "SELECT p.price, i.stock FROM products p JOIN inventory i ON p.id = i.product_id WHERE p.id = %s FOR UPDATE",
            (item_in.product_id,)
        )
        product_data = cursor.fetchone()
        if not product_data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        current_price, current_stock = product_data
        if current_stock < item_in.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {current_stock}")
        cursor.execute(
            """
            INSERT INTO order_items (order_id, product_id, qty, price_at_moment)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (order_id, product_id) DO UPDATE
            SET qty = order_items.qty + EXCLUDED.qty;
            """,
            (order_id, item_in.product_id, item_in.quantity, current_price)
        )
        cursor.execute(
            "UPDATE inventory SET stock = stock - %s WHERE product_id = %s",
            (item_in.quantity, item_in.product_id)
        )
        return _fetch_order_details(order_id, cursor)


@order_router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, conn: Connection = Depends(get_db_connection)):
    """[D]elete: Удаляет заказ и все его позиции (благодаря ON DELETE CASCADE)."""
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)