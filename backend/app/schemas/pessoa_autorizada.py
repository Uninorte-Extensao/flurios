from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.cpf import normalizar_cpf
from app.core.mascaramento import CpfMascarado


class PessoaAutorizadaCreate(BaseModel):
    """Ou informa nome e cpf, ou marca destinatario_e_a_pessoa (e nao informa nome/cpf).

    A combinacao e conferida no router, para que o erro 422 nao devolva o corpo
    da requisicao (que pode conter CPF).
    """

    destinatario_e_a_pessoa: bool = False
    nome: str | None = None
    cpf: str | None = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        return normalizar_cpf(valor)


class PessoaAutorizadaOut(BaseModel):
    id: int
    encomenda_id: int
    nome: str
    cpf: CpfMascarado
    criado_em: datetime

    class Config:
        from_attributes = True
