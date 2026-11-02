from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import usuario_logado
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteOut
from app.services.cliente import completar_cadastro_cliente

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def cadastrar_cliente(
    dados: ClienteCreate,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    try:
        return completar_cadastro_cliente(db, usuario, dados)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))
