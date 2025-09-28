from contextlib import contextmanager
import os
from urllib.parse import urlparse
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

url = urlparse(DATABASE_URL)

connection_pool = pool.SimpleConnectionPool(
    1, 10,
    dbname=url.path.lstrip("/"),
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)



def get_db_connection():
    conn = connection_pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e    
    finally:
        connection_pool.putconn(conn)