"""adiciona parada_destino_id em encomendas

Revision ID: c91d4e7a2b30
Revises: 7ceac32dc579
Create Date: 2026-11-05 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91d4e7a2b30'
down_revision: Union[str, Sequence[str], None] = '7ceac32dc579'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Nullable para nao quebrar encomendas ja existentes. A obrigatoriedade
    vale so na API (POST /encomendas). batch_alter_table porque o SQLite
    nao adiciona FK com ALTER TABLE.
    """
    with op.batch_alter_table('encomendas') as batch_op:
        batch_op.add_column(sa.Column('parada_destino_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_encomendas_parada_destino_id_paradas',
            'paradas',
            ['parada_destino_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('encomendas') as batch_op:
        batch_op.drop_constraint('fk_encomendas_parada_destino_id_paradas', type_='foreignkey')
        batch_op.drop_column('parada_destino_id')
