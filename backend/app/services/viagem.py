from sqlalchemy.orm import Session

from app.models.viagem import StatusViagem, Viagem
from app.schemas.viagem import ViagemCreate


def criar_viagem(db: Session, dados: ViagemCreate) -> Viagem:
    nova_viagem = Viagem(
        embarcacao_id=dados.embarcacao_id,
        rota_id=dados.rota_id,
        data_saida=dados.data_saida,
        status=StatusViagem.PROGRAMADA,
    )

    db.add(nova_viagem)
    db.commit()
    db.refresh(nova_viagem)

    return nova_viagem
