from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.viagem import StatusViagem
from app.schemas.embarcacao import EmbarcacaoOut
from app.schemas.rota import RotaDetalheOut


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


class ViagemDetalheOut(ViagemOut):
    embarcacao: EmbarcacaoOut
    rota: RotaDetalheOut


class LocalizacaoCreate(BaseModel):
    parada_id: int


class LocalizacaoOut(BaseModel):
    viagem_id: int
    parada_id: int
    encomendas_registradas: int
