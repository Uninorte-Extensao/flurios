from sqlalchemy.orm import Session

from app.models.encomenda import StatusEncomenda
from app.models.movimentacao import Movimentacao


def registrar_movimentacao(
    db: Session,
    encomenda_id: int,
    status: StatusEncomenda,
    viagem_id: int | None = None,
    parada_id: int | None = None,
) -> Movimentacao:
    """Adiciona uma movimentacao a sessao, sem commit.

    Quem chama e responsavel pelo commit, para que a movimentacao seja
    gravada na mesma transacao da mudanca que a originou.
    """
    movimentacao = Movimentacao(
        encomenda_id=encomenda_id,
        status=status,
        viagem_id=viagem_id,
        parada_id=parada_id,
    )

    db.add(movimentacao)

    return movimentacao
