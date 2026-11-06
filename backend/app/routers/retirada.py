from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.retirada import RetiradaCreate, RetiradaOut
from app.services.encomenda import buscar_encomenda_por_id
from app.services.retirada import (
    CpfNaoConfereError,
    TermoNaoAceitoError,
    registrar_retirada,
)

router = APIRouter(prefix="/encomendas", tags=["retirada"])


@router.post(
    "/{encomenda_id}/retirada",
    response_model=RetiradaOut,
    status_code=status.HTTP_201_CREATED,
)
def retirar_encomenda(
    encomenda_id: int,
    dados: RetiradaCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    """Registra a retirada (qualquer perfil da empresa) e marca como entregue."""
    encomenda = buscar_encomenda_por_id(db, encomenda_id)

    if encomenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomenda nao encontrada.",
        )

    try:
        retirada = registrar_retirada(
            db, encomenda, empresa, dados.cpf_retirante, dados.termo_aceito
        )
    except TermoNaoAceitoError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        )
    except CpfNaoConfereError as erro:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))

    return RetiradaOut(
        id=retirada.id,
        encomenda_id=retirada.encomenda_id,
        termo_aceito=retirada.termo_aceito,
        status_encomenda=encomenda.status,
        criado_em=retirada.criado_em,
    )
