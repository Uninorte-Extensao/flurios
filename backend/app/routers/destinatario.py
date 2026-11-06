from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import cliente_logado
from app.db.session import get_db
from app.models.cliente import Cliente
from app.schemas.destinatario import (
    DestinatarioCreate,
    DestinatarioDetalheOut,
    DestinatarioOut,
)
from app.services.destinatario import (
    buscar_destinatario_do_cliente,
    criar_destinatario,
    listar_destinatarios_do_cliente,
)

router = APIRouter(prefix="/destinatarios", tags=["destinatarios"])


@router.post("", response_model=DestinatarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar_destinatario(
    dados: DestinatarioCreate,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    return criar_destinatario(db, cliente.id, dados)


@router.get("", response_model=list[DestinatarioOut])
def listar_destinatarios(
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    return listar_destinatarios_do_cliente(db, cliente.id)


@router.get("/{destinatario_id}", response_model=DestinatarioDetalheOut)
def obter_destinatario(
    destinatario_id: int,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    destinatario = buscar_destinatario_do_cliente(db, destinatario_id, cliente.id)

    if destinatario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario nao encontrado.",
        )

    return destinatario
