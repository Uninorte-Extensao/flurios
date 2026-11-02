from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import cliente_logado
from app.core.mascaramento import mascarar_cpf
from app.db.session import get_db
from app.models.cliente import Cliente
from app.schemas.destinatario import (
    DestinatarioCreate,
    DestinatarioDetalheOut,
    DestinatarioOut,
)
from app.services.destinatario import buscar_destinatario_do_cliente, criar_destinatario

router = APIRouter(prefix="/destinatarios", tags=["destinatarios"])


@router.post("", response_model=DestinatarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar_destinatario(
    dados: DestinatarioCreate,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    return criar_destinatario(db, cliente.id, dados)


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

    resposta = DestinatarioDetalheOut.model_validate(destinatario)
    resposta.cpf = mascarar_cpf(resposta.cpf)

    return resposta
