import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db_connection, connection_pool

def override_get_db_connection():
    """
    Для каждого HTTP-запроса в тесте эта функция будет открывать
    соединение и делать COMMIT, точно так же, как "боевой" код.
    Это гарантирует, что данные, созданные в одном запросе,
    будут видны в следующем.
    """
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)

app.dependency_overrides[get_db_connection] = override_get_db_connection

@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield
    # print("\nCleaning up test data...")
    # conn = connection_pool.getconn()
    # with conn.cursor() as cursor:
    #     cursor.execute("TRUNCATE clients, categories, products, orders, order_items, inventory RESTART IDENTITY CASCADE;")
    # conn.commit()
    # connection_pool.putconn(conn)

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client