

from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from schemas.client import ClientCreate, ClientDelete, ClientResponse
from db.session import get_db_connection
from psycopg2.extensions import connection as Connection

client_router = APIRouter()

@client_router.get("/", response_model=List[ClientResponse])
def get_clients(conn: Connection = Depends(get_db_connection), skip: int = 0, limit: int = 100):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, address FROM clients OFFSET %s LIMIT %s", (skip, limit))
        rows = cursor.fetchall()
        return [ClientResponse(id=row[0], name=row[1], address=row[2]) for row in rows]



@client_router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, conn: Connection = Depends(get_db_connection)):
    with conn.cursor() as cursor:
        cursor.execute(
        """INSERT INTO clients (name, address)
        VALUES(%s, %s)
        RETURNING id, name, address
        """,
        (client.name, client.address)
    )
        row = cursor.fetchone()
        return ClientResponse(id=row[0], name=row[1], address=row[2])

@client_router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, conn: Connection = Depends(get_db_connection)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, address FROM clients WHERE id = %s", (client_id,))
        row = cursor.fetchone()
        if row:
            return ClientResponse(id=row[0], name=row[1], address=row[2])
        raise HTTPException(status_code=404, detail="Client not found")

@client_router.delete("/{client_id}", response_model=ClientDelete)
def delete_client(client_id: int, conn: Connection = Depends(get_db_connection)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM clients WHERE id = %s RETURNING id", (client_id,))
        row = cursor.fetchone()
        if row:
            return ClientDelete(id=row[0])
        raise HTTPException(status_code=404, detail="Client not found")