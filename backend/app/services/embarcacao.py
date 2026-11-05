from sqlalchemy.orm import Session

from app.models.embarcacao import Embarcacao
from app.models.viagem import Viagem
from app.schemas.embarcacao import EmbarcacaoCreate, EmbarcacaoUpdate

MENSAGEM_EMBARCACAO_COM_VIAGENS = (
    "Nao e possivel excluir uma embarcacao que ja possui viagens."
)


def criar_embarcacao(db: Session, dados: EmbarcacaoCreate) -> Embarcacao:
    nova_embarcacao = Embarcacao(nome=dados.nome, capacidade=dados.capacidade)

    db.add(nova_embarcacao)
    db.commit()
    db.refresh(nova_embarcacao)

    return nova_embarcacao


def listar_embarcacoes(db: Session) -> list[Embarcacao]:
    return db.query(Embarcacao).order_by(Embarcacao.nome).all()


def buscar_embarcacao_por_id(db: Session, embarcacao_id: int) -> Embarcacao | None:
    return db.query(Embarcacao).filter(Embarcacao.id == embarcacao_id).first()


def atualizar_embarcacao(
    db: Session,
    embarcacao: Embarcacao,
    dados: EmbarcacaoUpdate,
) -> Embarcacao:
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(embarcacao, campo, valor)

    db.commit()
    db.refresh(embarcacao)

    return embarcacao


def excluir_embarcacao(db: Session, embarcacao: Embarcacao) -> None:
    possui_viagens = (
        db.query(Viagem.id).filter(Viagem.embarcacao_id == embarcacao.id).first()
    )

    if possui_viagens is not None:
        raise ValueError(MENSAGEM_EMBARCACAO_COM_VIAGENS)

    db.delete(embarcacao)
    db.commit()
