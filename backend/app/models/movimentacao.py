from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.encomenda import StatusEncomenda


class Movimentacao(Base):
    """Registro do historico de uma encomenda: o status que ela assumiu,
    e, quando houver, a parada e a viagem em que isso aconteceu."""

    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    encomenda_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encomendas.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[StatusEncomenda] = mapped_column(
        Enum(
            StatusEncomenda,
            name="status_movimentacao",
            native_enum=False,
            create_constraint=True,
            length=30,
            validate_strings=True,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        nullable=False,
    )
    parada_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("paradas.id"),
        nullable=True,
    )
    viagem_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("viagens.id"),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
