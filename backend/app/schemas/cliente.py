from datetime import datetime

from pydantic import BaseModel, Field

class ClienteCreate(BaseModel):
    cpf: str = Field(min_length=11, max_length=11)
    telefone: str


class ClienteOut(BaseModel):
    id: int
    usuario_id: int
    cpf: str
    telefone: str
    criado_em: datetime

    class Config:
        from_attributes = True
