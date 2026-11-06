from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.models.embarcacao import Embarcacao
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.rota import Rota
from app.models.viagem import StatusViagem, Viagem
from app.models.viagem_encomenda import ViagemEncomenda

# Encomenda que ainda ocupa espaco na embarcacao: nem entregue, nem em imprevisto.
STATUS_ENCOMENDA_FORA_DA_OCUPACAO = (StatusEncomenda.ENTREGUE, StatusEncomenda.IMPREVISTO)


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


def calcular_ocupacao_viagens_em_andamento(db: Session) -> list[dict]:
    """Ocupacao de cada viagem em andamento.

    Convencao: a capacidade da embarcacao e um numero de encomendas. Ocupacao =
    encomendas ativas associadas a viagem / capacidade. "Ativa" = nao entregue e
    nao imprevisto.
    """
    ativas = func.count(Encomenda.id)
    linhas = (
        db.query(Viagem, Embarcacao, Rota.nome, ativas)
        .join(Embarcacao, Embarcacao.id == Viagem.embarcacao_id)
        .join(Rota, Rota.id == Viagem.rota_id)
        .outerjoin(ViagemEncomenda, ViagemEncomenda.viagem_id == Viagem.id)
        .outerjoin(
            Encomenda,
            (Encomenda.id == ViagemEncomenda.encomenda_id)
            & Encomenda.status.notin_(STATUS_ENCOMENDA_FORA_DA_OCUPACAO),
        )
        .filter(Viagem.status == StatusViagem.EM_ANDAMENTO)
        .group_by(Viagem.id, Embarcacao.id, Rota.nome)
        .order_by(Viagem.data_saida, Viagem.id)
        .all()
    )

    return [
        {
            "viagem_id": viagem.id,
            "embarcacao_id": embarcacao.id,
            "embarcacao_nome": embarcacao.nome,
            "rota_nome": rota_nome,
            "capacidade": embarcacao.capacidade,
            "encomendas_ativas": total,
            "ocupacao": round(total / embarcacao.capacidade, 4) if embarcacao.capacidade else 0.0,
        }
        for viagem, embarcacao, rota_nome, total in linhas
    ]
