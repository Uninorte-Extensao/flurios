from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.schemas.destinatario import DestinatarioCreate

def criar_destinatario(db: Session, dados: DestinatarioCreate) -> Destinatario:
    novo_destinatario = Destinatario(
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
