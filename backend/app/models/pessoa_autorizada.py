from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PessoaAutorizada(Base):
    """Pessoa autorizada a retirar uma encomenda. Uma por encomenda.

    O CPF e guardado completo (11 digitos), mas nunca deve sair completo
    pela API nem ir para log: use app.core.mascaramento.mascarar_cpf.
    """

    __tablename__ = "pessoas_autorizadas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    encomenda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encomendas.id"),
        unique=True,
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
