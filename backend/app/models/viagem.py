import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StatusViagem(str, enum.Enum):
    PROGRAMADA = "programada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


# Viagem "ativa" = ainda pode receber/transportar encomendas.
STATUS_VIAGEM_ATIVOS = (StatusViagem.PROGRAMADA, StatusViagem.EM_ANDAMENTO)


class Viagem(Base):
    __tablename__ = "viagens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    embarcacao_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("embarcacoes.id"),
        nullable=False,
    )
    rota_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rotas.id"),
        nullable=False,
    )
    data_saida: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[StatusViagem] = mapped_column(
        Enum(
            StatusViagem,
            name="status_viagem",
            native_enum=False,
            create_constraint=True,
            length=30,
            validate_strings=True,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        default=StatusViagem.PROGRAMADA,
        nullable=False,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
