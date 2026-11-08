from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import cliente_logado, empresa_logado, usuario_logado
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.encomenda import StatusEncomenda
from app.schemas.movimentacao import RastreioOut
from app.services.cliente import buscar_cliente_por_usuario
from app.services.empresa import buscar_empresa_por_usuario
from app.services.movimentacao import listar_historico_da_encomenda
from app.schemas.encomenda import EncomendaCreate, EncomendaOut, EncomendaStatusUpdate
from app.services.destinatario import buscar_destinatario_do_cliente
from app.services.parada import ORDEM_ORIGEM, buscar_parada_por_id
from app.services.encomenda import (
    atualizar_status_encomenda,
    buscar_encomenda_do_cliente,
    buscar_encomenda_por_codigo,
    buscar_encomenda_por_id,
    criar_encomenda,
    listar_encomendas_do_cliente,
)

router = APIRouter(prefix="/encomendas", tags=["encomendas"])

MENSAGEM_ENTREGUE_SO_PELA_RETIRADA = (
    "O status entregue so e registrado pela retirada da encomenda."
)


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

    parada_destino = buscar_parada_por_id(db, dados.parada_destino_id)

    if parada_destino is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parada de destino nao encontrada.",
        )

    if parada_destino.ordem == ORDEM_ORIGEM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A parada de origem nao pode ser o destino da encomenda.",
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


@router.get("/{codigo}/rastreio", response_model=RastreioOut)
def rastrear_encomenda(
    codigo: str,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    """Historico completo. Empresa ve qualquer codigo; cliente, so os seus."""
    if buscar_empresa_por_usuario(db, usuario.id) is not None:
        encomenda = buscar_encomenda_por_codigo(db, codigo)
    else:
        cliente = buscar_cliente_por_usuario(db, usuario.id)

        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario sem cadastro de cliente ou empresa.",
            )

        encomenda = buscar_encomenda_do_cliente(db, codigo, cliente.id)

    if encomenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomenda nao encontrada.",
        )

    return RastreioOut(
        codigo_rastreio=encomenda.codigo_rastreio,
        status_atual=encomenda.status,
        historico=listar_historico_da_encomenda(db, encomenda.id),
    )


@router.patch("/{encomenda_id}/status", response_model=EncomendaOut)
def atualizar_status(
    encomenda_id: int,
    dados: EncomendaStatusUpdate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    """Muda o status manualmente. `entregue` fica de fora: so a retirada o gera."""
    if dados.status == StatusEncomenda.ENTREGUE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=MENSAGEM_ENTREGUE_SO_PELA_RETIRADA,
        )

    encomenda = buscar_encomenda_por_id(db, encomenda_id)

    if encomenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomenda nao encontrada.",
        )

    return atualizar_status_encomenda(db, encomenda, dados.status)
