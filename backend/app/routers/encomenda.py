from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import cliente_logado
from app.db.session import get_db
from app.models.cliente import Cliente
from app.schemas.encomenda import EncomendaCreate, EncomendaOut
from app.services.destinatario import buscar_destinatario_do_cliente
from app.services.encomenda import (
    buscar_encomenda_do_cliente,
    criar_encomenda,
    listar_encomendas_do_cliente,
)

router = APIRouter(prefix="/encomendas", tags=["encomendas"])


@router.post("", response_model=EncomendaOut, status_code=status.HTTP_201_CREATED)
def cadastrar_encomenda(
    dados: EncomendaCreate,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    destinatario = buscar_destinatario_do_cliente(db, dados.destinatario_id, cliente.id)

    if destinatario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario nao encontrado.",
        )

    return criar_encomenda(db, cliente, destinatario, dados)


@router.get("", response_model=list[EncomendaOut])
def listar_encomendas(
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    return listar_encomendas_do_cliente(db, cliente.id)


@router.get("/{codigo}", response_model=EncomendaOut)
def buscar_encomenda(
    codigo: str,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    encomenda = buscar_encomenda_do_cliente(db, codigo, cliente.id)

    if encomenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomenda nao encontrada.",
        )

    return encomenda
