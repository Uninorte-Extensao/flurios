from sqlalchemy.orm import Session

from app.models.parada import Parada
from app.models.rota import Rota
from app.schemas.parada import ParadaCreate, ParadaUpdate

MENSAGEM_ORDEM_REPETIDA = "Ja existe uma parada com essa ordem na rota."
# A parada de ordem 1 e a origem (Manaus): nunca pode ser destino de encomenda.
ORDEM_ORIGEM = 1


def buscar_parada_da_rota(db: Session, rota_id: int, parada_id: int) -> Parada | None:
    return (
        db.query(Parada)
        .filter(Parada.id == parada_id, Parada.rota_id == rota_id)
        .first()
    )


def listar_paradas_da_rota(db: Session, rota_id: int) -> list[Parada]:
    return (
        db.query(Parada)
        .filter(Parada.rota_id == rota_id)
        .order_by(Parada.ordem)
        .all()
    )


def ordem_ja_usada(
    db: Session,
    rota_id: int,
    ordem: int,
    ignorar_parada_id: int | None = None,
) -> bool:
    consulta = db.query(Parada).filter(Parada.rota_id == rota_id, Parada.ordem == ordem)

    if ignorar_parada_id is not None:
        consulta = consulta.filter(Parada.id != ignorar_parada_id)

    return consulta.first() is not None


def criar_parada(db: Session, rota_id: int, dados: ParadaCreate) -> Parada:
    if ordem_ja_usada(db, rota_id, dados.ordem):
        raise ValueError(MENSAGEM_ORDEM_REPETIDA)

    nova_parada = Parada(rota_id=rota_id, nome=dados.nome, ordem=dados.ordem)

    db.add(nova_parada)
    db.commit()
    db.refresh(nova_parada)

    return nova_parada


def atualizar_parada(db: Session, parada: Parada, dados: ParadaUpdate) -> Parada:
    alteracoes = {
        campo: valor
        for campo, valor in dados.model_dump(exclude_unset=True).items()
        if valor is not None
    }

    nova_ordem = alteracoes.get("ordem")
    if nova_ordem is not None and ordem_ja_usada(
        db, parada.rota_id, nova_ordem, ignorar_parada_id=parada.id
    ):
        raise ValueError(MENSAGEM_ORDEM_REPETIDA)

    for campo, valor in alteracoes.items():
        setattr(parada, campo, valor)

    db.commit()
    db.refresh(parada)

    return parada


def excluir_parada(db: Session, parada: Parada) -> None:
    db.delete(parada)
    db.commit()


def buscar_parada_por_id(db: Session, parada_id: int) -> Parada | None:
    return db.query(Parada).filter(Parada.id == parada_id).first()


def listar_destinos(db: Session) -> list[tuple[Parada, Rota]]:
    """Paradas de todas as rotas, menos a de ordem 1 (origem)."""
    return (
        db.query(Parada, Rota)
        .join(Rota, Parada.rota_id == Rota.id)
        .filter(Parada.ordem != ORDEM_ORIGEM)
        .order_by(Rota.nome, Parada.ordem)
        .all()
    )
