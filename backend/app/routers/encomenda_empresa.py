from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.models.encomenda import StatusEncomenda
from app.schemas.encomenda import EncomendaEmpresaListaOut
from app.services.encomenda import listar_encomendas_da_empresa

# Prefixo proprio: GET /encomendas/{codigo} e do cliente e nao pode colidir.
router = APIRouter(prefix="/empresa/encomendas", tags=["encomendas (empresa)"])


@router.get("", response_model=EncomendaEmpresaListaOut)
def listar_encomendas(
    status: list[StatusEncomenda] | None = Query(default=None),
    parada_destino_id: int | None = Query(default=None),
    rota_id: int | None = Query(default=None),
    sem_viagem_ativa: bool = Query(default=False),
    busca: str | None = Query(default=None, max_length=30),
    limite: int = Query(default=20, ge=1, le=100),
    deslocamento: int = Query(default=0, ge=0),
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    """Encomendas de todos os clientes para a empresa, com filtros e paginacao."""
    itens, total = listar_encomendas_da_empresa(
        db,
        status=status,
        parada_destino_id=parada_destino_id,
        rota_id=rota_id,
        sem_viagem_ativa=sem_viagem_ativa,
        busca=busca,
        limite=limite,
        deslocamento=deslocamento,
    )

    return EncomendaEmpresaListaOut(
        itens=itens, total=total, limite=limite, deslocamento=deslocamento
    )
