from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmbarcacaoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    capacidade: int = Field(gt=0)


class EmbarcacaoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    capacidade: int | None = Field(default=None, gt=0)
    ativa: bool | None = None


class EmbarcacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    capacidade: int
    ativa: bool
    criado_em: datetime
