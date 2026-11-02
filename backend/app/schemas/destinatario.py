from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.cpf import normalizar_cpf

class DestinatarioCreate(BaseModel):
    nome: str
    cpf: str
    telefone: str
    endereco: str
    municipio: str

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_cpf(valor)


class DestinatarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    telefone: str
    endereco: str
    municipio: str
    criado_em: datetime

    class Config:
        from_attributes = True


class DestinatarioDetalheOut(DestinatarioOut):
    """Mesmo formato de DestinatarioOut, mas com o CPF sempre mascarado."""
