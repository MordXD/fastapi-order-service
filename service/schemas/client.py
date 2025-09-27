from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    adress: str

class ClientResponse(BaseModel):
    id: int
    name: str
    adress: str

    class Config:
        from_attributes = True
