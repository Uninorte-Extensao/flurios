from sqlalchemy.orm import Session

from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import Viagem
from app.schemas.rota import RotaCreate, RotaUpdate

MENSAGEM_ROTA_COM_VIAGENS = "Nao e possivel excluir uma rota que ja possui viagens."


def criar_rota(db: Session, dados: RotaCreate) -> Rota:
    nova_rota = Rota(nome=dados.nome)

    db.add(nova_rota)
    db.commit()
    db.refresh(nova_rota)

    return nova_rota


def listar_rotas(db: Session) -> list[Rota]:
    return db.query(Rota).order_by(Rota.nome).all()


def buscar_rota_por_id(db: Session, rota_id: int) -> Rota | None:
    return db.query(Rota).filter(Rota.id == rota_id).first()


def atualizar_rota(db: Session, rota: Rota, dados: RotaUpdate) -> Rota:
    if dados.nome is not None:
        rota.nome = dados.nome

    db.commit()
    db.refresh(rota)

    return rota


def excluir_rota(db: Session, rota: Rota) -> None:
    possui_viagens = db.query(Viagem.id).filter(Viagem.rota_id == rota.id).first()

    if possui_viagens is not None:
        raise ValueError(MENSAGEM_ROTA_COM_VIAGENS)

    db.query(Parada).filter(Parada.rota_id == rota.id).delete()
    db.delete(rota)
    db.commit()
