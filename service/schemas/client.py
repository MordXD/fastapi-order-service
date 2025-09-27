from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    address: str

class ClientDelete(BaseModel):
    id: int

class ClientResponse(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        from_attributes = True
