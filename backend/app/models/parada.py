from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parada(Base):
    __tablename__ = "paradas"
    __table_args__ = (UniqueConstraint("rota_id", "ordem", name="uq_paradas_rota_ordem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rota_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rotas.id"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
