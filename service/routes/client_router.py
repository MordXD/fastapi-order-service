

from typing import List
from fastapi import APIRouter
from fastapi import Depends
from schemas.client import ClientResponse
from db.session import get_db_connection

client_router = APIRouter()

@client_router.get("/", response_model=List[ClientResponse])
async def list_clients(cursor =  Depends(get_db_connection)):
    cursor.execute("SELECT id, name, address FROM clients")
    rows = cursor.fetchall()
    return [ClientResponse(id=row[0], name=row[1], adress=row[2]) for row in rows]
