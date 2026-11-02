from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import usuario_logado
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.destinatario import DestinatarioCreate, DestinatarioOut
from app.services.destinatario import criar_destinatario

router = APIRouter(prefix="/destinatarios", tags=["destinatarios"])


@router.post("", response_model=DestinatarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar_destinatario(
    dados: DestinatarioCreate,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    return criar_destinatario(db, dados)
