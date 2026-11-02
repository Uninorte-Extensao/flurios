from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.schemas.destinatario import DestinatarioCreate

def criar_destinatario(
    db: Session,
    cliente_id: int,
    dados: DestinatarioCreate,
) -> Destinatario:
    novo_destinatario = Destinatario(
        cliente_id=cliente_id,
        nome=dados.nome,
        cpf=dados.cpf,
        telefone=dados.telefone,
        endereco=dados.endereco,
        municipio=dados.municipio,
    )

    db.add(novo_destinatario)
    db.commit()
    db.refresh(novo_destinatario)

    return novo_destinatario


def buscar_destinatario_do_cliente(
    db: Session,
    destinatario_id: int,
    cliente_id: int,
) -> Destinatario | None:
    return (
        db.query(Destinatario)
        .filter(
            Destinatario.id == destinatario_id,
            Destinatario.cliente_id == cliente_id,
        )
        .first()
    )
