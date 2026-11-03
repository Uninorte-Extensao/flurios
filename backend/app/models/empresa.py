import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class PerfilEmpresa(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    ATENDENTE = "atendente"
    OPERADOR_EMBARCACAO = "operador_embarcacao"
    FUNCIONARIO_RETIRADA = "funcionario_retirada"


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=False,
    )
    perfil: Mapped[PerfilEmpresa] = mapped_column(
        Enum(
            PerfilEmpresa,
            name="perfil_empresa",
            native_enum=False,
            create_constraint=True,
            length=30,
            validate_strings=True,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        nullable=False,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    usuario = relationship("Usuario")
