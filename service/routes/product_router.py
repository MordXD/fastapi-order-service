


from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import List
from psycopg2.extensions import connection as Connection
from schemas.product import ProductCreate, ProductResponse, ProductUpdate

from db.session import get_db_connection

product_router = APIRouter()


@product_router.get("/", response_model=List[ProductResponse])
def get_products(conn: Connection = Depends(get_db_connection), skip: int = 0, limit: int = 100):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.id, p.name, p.price, p.category_id, COALESCE(i.stock, 0) as stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            ORDER BY p.id
            OFFSET %s LIMIT %s
            """,
            (skip, limit)
        )
        rows = cursor.fetchall()
        return [ProductResponse(id=row[0], name=row[1], price=row[2], category_id=row[3], stock=row[4]) for row in rows]
    

@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, conn: Connection = Depends(get_db_connection)):
    """Создает товар и связанную с ним запись об остатках."""
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO products (name, price, category_id)
            VALUES (%s, %s, %s)
            RETURNING id, name, price, category_id
            """,
            (product.name, product.price, product.category_id)
        )
        product_row = cursor.fetchone()
        new_product_id = product_row[0]
        
        initial_stock = product.initial_stock if hasattr(product, 'initial_stock') else 0
        cursor.execute(
            """INSERT INTO inventory (product_id, stock)
            VALUES (%s, %s)
            """,
            (new_product_id, initial_stock)
        )
        return ProductResponse(
            id=product_row[0], name=product_row[1], price=product_row[2], category_id=product_row[3], stock=initial_stock
        )
        
@product_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, conn: Connection = Depends(get_db_connection)):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.id, p.name, p.price, p.category_id, COALESCE(i.stock, 0) as stock
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id = %s
            """,
            (product_id,)
        )
        row = cursor.fetchone()
        if row:
            return ProductResponse(id=row[0], name=row[1], price=row[2], category_id=row[3], stock=row[4])
        raise HTTPException(status_code=404, detail="Product not found")

@product_router.patch("/{product_id}", response_model=ProductResponse)
def update_product_info(product_id: int, product_update: ProductUpdate, conn: Connection = Depends(get_db_connection)):
    """Обновляет только информацию о товаре (каталог), не трогая остатки."""
    with conn.cursor() as cursor:
        cursor.execute(
            """ WITH updated_product AS (
                    UPDATE products
                    SET name = %s, price = %s, category_id = %s
                    WHERE id = %s
                    RETURNING id, name, price, category_id
                )
                SELECT 
                    up.id, up.name, up.price, up.category_id, i.stock
                FROM updated_product up
                JOIN inventory i ON up.id = i.product_id;  
            """,
            (product_update.name, product_update.price, product_update.category_id, product_id)
        )
        row = cursor.fetchone()
        if row:
            return ProductResponse(id=row[0], name=row[1], price=row[2], category_id=row[3], stock=row[4])
        raise HTTPException(status_code=404, detail="Product Not Found")
        

@product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, conn: Connection = Depends(get_db_connection)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product Not Found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)