from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.parada import ParadaOut


class RotaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)


class RotaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)


class RotaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    criado_em: datetime


class RotaDetalheOut(RotaOut):
    paradas: list[ParadaOut] = []
