from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.cpf import normalizar_cpf
from app.models.encomenda import StatusEncomenda


class RetiradaCreate(BaseModel):
    """CPF digitado na hora por quem retira e aceite do termo de compromisso.

    termo_aceito tem padrao False de proposito: o service recusa a retirada sem
    o aceite e o erro 422 nao devolve o corpo da requisicao (que contem CPF).
    """

    cpf_retirante: str
    termo_aceito: bool = False

    @field_validator("cpf_retirante")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_cpf(valor)


class RetiradaOut(BaseModel):
    id: int
    encomenda_id: int
    termo_aceito: bool
    status_encomenda: StatusEncomenda
    criado_em: datetime
