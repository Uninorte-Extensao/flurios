from pydantic import BaseModel, EmailStr

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