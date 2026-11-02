from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.services.usuario import criar_usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return criar_usuario(db, dados)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))
