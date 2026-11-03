from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_administrador
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaOut
from app.services.empresa import completar_cadastro_empresa
from app.services.usuario import buscar_usuario_por_email

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.post("", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
def cadastrar_empresa(
    dados: EmpresaCreate,
    administrador: Empresa = Depends(empresa_administrador),
    db: Session = Depends(get_db),
):
    usuario = buscar_usuario_por_email(db, dados.email)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    try:
        return completar_cadastro_empresa(db, usuario, dados.perfil)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))
