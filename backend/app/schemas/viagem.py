from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.viagem import StatusViagem


class ViagemCreate(BaseModel):
    embarcacao_id: int
    rota_id: int
    data_saida: datetime


class ViagemStatusUpdate(BaseModel):
    status: StatusViagem


class ViagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    embarcacao_id: int
    rota_id: int
    data_saida: datetime
    status: StatusViagem
    criado_em: datetime


class ViagemEncomendaCreate(BaseModel):
    encomenda_id: int


class ViagemEncomendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    viagem_id: int
    encomenda_id: int
    criado_em: datetime
