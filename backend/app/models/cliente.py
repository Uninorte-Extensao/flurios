from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=False,
    )
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    usuario = relationship("Usuario")
