import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class StatusEncomenda(str, enum.Enum):
    PENDENTE = "pendente"
    RECEBIDA = "recebida"
    AGUARDANDO_EMBARQUE = "aguardando_embarque"
    EMBARCADA = "embarcada"
    EM_TRANSITO = "em_transito"
    CHEGOU_AO_DESTINO = "chegou_ao_destino"
    A_RETIRAR = "a_retirar"
    ENTREGUE = "entregue"
    IMPREVISTO = "imprevisto"


class Encomenda(Base):
    __tablename__ = "encomendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False,
    )
    destinatario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("destinatarios.id"),
        nullable=False,
    )
    # Nullable so encomendas antigas (sem destino) continuam validas no banco.
    # A API exige o campo em POST /encomendas.
    parada_destino_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("paradas.id"),
        nullable=True,
    )
    codigo_rastreio: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[StatusEncomenda] = mapped_column(
        Enum(
            StatusEncomenda,
            name="status_encomenda",
            native_enum=False,
            create_constraint=True,
            length=30,
            validate_strings=True,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        default=StatusEncomenda.PENDENTE,
        nullable=False,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    parada_destino = relationship("Parada")
    destinatario = relationship("Destinatario")

    @property
    def destino_nome(self) -> str | None:
        return self.parada_destino.nome if self.parada_destino else None
