from datetime import datetime

from pydantic import BaseModel, Field

class DestinatarioCreate(BaseModel):
    nome: str
    cpf: str = Field(min_length=11, max_length=11)
    telefone: str
    endereco: str
    municipio: str


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
