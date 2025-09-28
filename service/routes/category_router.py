
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from psycopg2.extensions import connection as Connection, cursor as Cursor
from db.session import get_db_connection
from schemas.category import CategoryCreate, CategoryResponse, CategoryTreeNode

category_router = APIRouter()


@category_router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_in: CategoryCreate, conn: Connection = Depends(get_db_connection)):
    """Создает новую категорию и вычисляет ее ltree путь."""
    with conn.cursor() as cursor:
        # Шаг 1: Вставляем новую категорию, используя временный путь,
        # который мы сразу же получим из RETURNING id.
        # Мы не можем сразу вычислить полный путь, так как не знаем id.
        cursor.execute(
            """
            INSERT INTO categories (name, parent_id, path)
            -- Вставляем временный 'placeholder' путь.
            -- Он будет заменен на правильный через мгновение.
            VALUES (%s, %s, 'tmp')
            RETURNING id
            """,
            (category_in.name, category_in.parent_id)
        )
        new_category_id = cursor.fetchone()[0]

        # Шаг 2: Вычисляем правильный путь
        parent_path_str = ""
        if category_in.parent_id:
            cursor.execute("SELECT path FROM categories WHERE id = %s", (category_in.parent_id,))
            parent_row = cursor.fetchone()
            if not parent_row:
                # Этого не должно произойти, так как у нас есть FK constraint, но для надежности.
                raise HTTPException(status_code=404, detail="Parent category not found")
            parent_path_str = str(parent_row[0]) + "."

        new_path = f"{parent_path_str}{new_category_id}"

        # Шаг 3: Обновляем запись правильным путем ltree
        cursor.execute(
            "UPDATE categories SET path = %s::ltree WHERE id = %s RETURNING id, name, path, parent_id",
            (new_path, new_category_id)
        )
        
        # RETURNING в UPDATE сразу вернет нам все нужные данные для ответа
        final_row = cursor.fetchone()

        return CategoryResponse(
            id=final_row[0],
            name=final_row[1],
            path=str(final_row[2]), # Преобразуем ltree в строку для Pydantic
            parent_id=final_row[3]
        )


@category_router.get("/tree", response_model=List[CategoryTreeNode])
def get_category_tree(conn: Connection = Depends(get_db_connection)):
    """Возвращает полное дерево категорий."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, path, parent_id FROM categories ORDER BY path")
        all_categories = cursor.fetchall()
        nodes = {
            row[0]: CategoryTreeNode(
                id=row[0], name=row[1], path=row[2], parent_id=row[3], children=[]
            ) for row in all_categories
        }
        tree = []
        for cat_id, node in nodes.items():
            if node.parent_id:
                parent = nodes.get(node.parent_id)
                if parent:
                    parent.children.append(node)
            else:
                tree.append(node)
        
        return tree


@category_router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, conn: Connection = Depends(get_db_connection)):
    """Получает информацию о конкретной категории."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, path, parent_id FROM categories WHERE id = %s",
            (category_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return CategoryResponse(id=row[0], name=row[1], path=row[2], parent_id=row[3])


@category_router.get("/{category_id}/children", response_model=List[CategoryResponse])
def get_category_children(category_id: int, conn: Connection = Depends(get_db_connection)):
    """
    Получает всех прямых потомков (дочерние категории) для указанной категории.
    Использует мощь ltree!
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT path FROM categories WHERE id = %s", (category_id,))
        path_row = cursor.fetchone()
        if not path_row:
            raise HTTPException(status_code=404, detail="Category not found")
        parent_path = path_row[0]
        cursor.execute(
            """
            SELECT id, name, path, parent_id
            FROM categories
            WHERE path <@ %s AND nlevel(path) = nlevel(%s) + 1
            ORDER BY name
            """,
            (parent_path, parent_path)
        )
        rows = cursor.fetchall()
        return [CategoryResponse(id=row[0], name=row[1], path=row[2], parent_id=row[3]) for row in rows]


@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, conn: Connection = Depends(get_db_connection)):
    """
    Удаляет категорию. Благодаря 'ON DELETE CASCADE' в БД,
    все дочерние категории будут также удалены автоматически.
    """
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)