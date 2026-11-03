from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.empresa import PerfilEmpresa

class EmpresaCreate(BaseModel):
    email: EmailStr
    perfil: PerfilEmpresa


class EmpresaOut(BaseModel):
    id: int
    usuario_id: int
    perfil: PerfilEmpresa
    criado_em: datetime

    class Config:
        from_attributes = True
