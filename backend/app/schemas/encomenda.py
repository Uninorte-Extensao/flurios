from datetime import datetime

from pydantic import BaseModel, Field

from app.core.mascaramento import CpfMascarado
from app.models.encomenda import StatusEncomenda
from app.models.viagem import StatusViagem


class EncomendaCreate(BaseModel):
    destinatario_id: int
    parada_destino_id: int
    descricao: str = Field(min_length=1, max_length=255)


class EncomendaStatusUpdate(BaseModel):
    status: StatusEncomenda


class EncomendaOut(BaseModel):
    id: int
    cliente_id: int
    destinatario_id: int
    parada_destino_id: int | None
    destino_nome: str | None
    codigo_rastreio: str
    descricao: str
    status: StatusEncomenda
    criado_em: datetime

    class Config:
        from_attributes = True


class DestinatarioResumoOut(BaseModel):
    """Destinatario na listagem da empresa. O CPF sai sempre mascarado."""

    nome: str
    cpf: CpfMascarado


class ViagemAtivaResumoOut(BaseModel):
    id: int
    status: StatusViagem
    data_saida: datetime


class EncomendaEmpresaOut(BaseModel):
    id: int
    codigo_rastreio: str
    status: StatusEncomenda
    descricao: str
    destinatario: DestinatarioResumoOut
    parada_destino_id: int | None
    destino_nome: str | None
    criado_em: datetime
    viagem_ativa: ViagemAtivaResumoOut | None


class EncomendaEmpresaListaOut(BaseModel):
    itens: list[EncomendaEmpresaOut]
    total: int
    limite: int
    deslocamento: int
