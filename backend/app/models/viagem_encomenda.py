from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ViagemEncomenda(Base):
    __tablename__ = "viagem_encomendas"
    __table_args__ = (
        UniqueConstraint("viagem_id", "encomenda_id", name="uq_viagem_encomendas_par"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    viagem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("viagens.id"),
        nullable=False,
    )
    encomenda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encomendas.id"),
        nullable=False,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
