from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.viagem import StatusViagem, Viagem


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


def contar_viagens_por_status(db: Session) -> dict[str, int]:
    """Contagem de viagens por status. Todos os status aparecem (zero se nao ha)."""
    linhas = (
        db.query(Viagem.status, func.count(Viagem.id))
        .group_by(Viagem.status)
        .all()
    )
    contagem = {status.value: 0 for status in StatusViagem}

    for status, total in linhas:
        contagem[status.value] = total

    return contagem


def contar_encomendas_por_municipio(db: Session) -> list[tuple[str, int]]:
    """Encomendas por municipio de destino, do maior para o menor total."""
    return (
        db.query(Destinatario.municipio, func.count(Encomenda.id))
        .join(Encomenda, Encomenda.destinatario_id == Destinatario.id)
        .group_by(Destinatario.municipio)
        .order_by(func.count(Encomenda.id).desc(), Destinatario.municipio)
        .all()
    )
