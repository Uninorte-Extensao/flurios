from pydantic import BaseModel, ConfigDict, Field


class ParadaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    ordem: int = Field(gt=0)


class ParadaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    ordem: int | None = Field(default=None, gt=0)


class ParadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rota_id: int
    nome: str
    ordem: int
