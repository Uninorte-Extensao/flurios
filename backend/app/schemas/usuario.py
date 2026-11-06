from typing import Literal

from pydantic import BaseModel, EmailStr

from app.models.empresa import PerfilEmpresa

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str


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
