from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Retirada(Base):
    """Registro da retirada de uma encomenda no ponto de retirada. Uma por encomenda.

    O CPF de quem retirou e guardado completo (11 digitos), mas nunca deve
    sair completo pela API nem ir para log: use app.core.mascaramento.mascarar_cpf.
    """

    __tablename__ = "retiradas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    encomenda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encomendas.id"),
        unique=True,
        nullable=False,
    )
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
    )
    cpf_retirante: Mapped[str] = mapped_column(String(11), nullable=False)
    termo_aceito: Mapped[bool] = mapped_column(Boolean, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
