from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.cpf import normalizar_cpf

class ClienteCreate(BaseModel):
    cpf: str
    telefone: str

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_cpf(valor)


class ClienteOut(BaseModel):
    id: int
    usuario_id: int
    cpf: str
    telefone: str
    criado_em: datetime

    class Config:
        from_attributes = True
