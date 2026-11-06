from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.encomenda import Encomenda, StatusEncomenda


def contar_encomendas_por_status(db: Session) -> dict[str, int]:
    """Contagem de encomendas por status. Todos os status aparecem (zero se nao ha)."""
    linhas = (
        db.query(Encomenda.status, func.count(Encomenda.id))
        .group_by(Encomenda.status)
        .all()
    )
    contagem = {status.value: 0 for status in StatusEncomenda}

    for status, total in linhas:
        contagem[status.value] = total

    return contagem
