"""adiciona validacao de status em encomendas

Revision ID: 773383972fea
Revises: be1c1b11c626
Create Date: 2026-11-02 21:15:56.388465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '773383972fea'
down_revision: Union[str, Sequence[str], None] = 'be1c1b11c626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STATUS_VALIDOS = (
    "pendente",
    "recebida",
    "aguardando_embarque",
    "embarcada",
    "em_transito",
    "chegou_ao_destino",
    "a_retirar",
    "entregue",
    "imprevisto",
)


def upgrade() -> None:
    """Upgrade schema."""
    lista_status = ", ".join(f"'{status}'" for status in STATUS_VALIDOS)

    with op.batch_alter_table("encomendas") as batch_op:
        batch_op.create_check_constraint(
            "ck_encomendas_status_valido",
            f"status IN ({lista_status})",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("encomendas") as batch_op:
        batch_op.drop_constraint("ck_encomendas_status_valido", type_="check")
