from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.models.empresa import PerfilEmpresa

SENHA_MINIMA = 6


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

    # So no cadastro: o login (LoginRequest) nao valida o tamanho, para nao
    # barrar contas criadas antes desta regra.
    @field_validator("senha")
    @classmethod
    def validar_tamanho_da_senha(cls, senha: str) -> str:
        if len(senha) < SENHA_MINIMA:
            raise ValueError(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")

        return senha


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    ativo: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioMeOut(BaseModel):
    """Usuario logado: o tipo de conta e, para empresa, o perfil.

    `tipo` e None quando o usuario ainda nao completou o cadastro
    (nem cliente, nem empresa). Nao devolve CPF nem telefone.
    """

    id: int
    nome: str
    email: EmailStr
    tipo: Literal["cliente", "empresa"] | None
    perfil: PerfilEmpresa | None = None
