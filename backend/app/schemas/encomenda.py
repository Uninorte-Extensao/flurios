from datetime import datetime

from pydantic import BaseModel

from app.models.encomenda import StatusEncomenda

class EncomendaCreate(BaseModel):
    destinatario_id: int
    descricao: str


class EncomendaOut(BaseModel):
    id: int
    cliente_id: int
    destinatario_id: int
    codigo_rastreio: str
    descricao: str
    status: StatusEncomenda
    criado_em: datetime

    class Config:
        from_attributes = True
