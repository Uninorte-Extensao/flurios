from datetime import datetime

from pydantic import BaseModel

from app.models.encomenda import StatusEncomenda


class MovimentacaoOut(BaseModel):
    id: int
    status: StatusEncomenda
    parada_id: int | None
    parada_nome: str | None
    viagem_id: int | None
    criado_em: datetime


class RastreioOut(BaseModel):
    codigo_rastreio: str
    status_atual: StatusEncomenda
    historico: list[MovimentacaoOut]
