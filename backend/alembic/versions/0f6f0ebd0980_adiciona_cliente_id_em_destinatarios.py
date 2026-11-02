"""adiciona cliente_id em destinatarios

Revision ID: 0f6f0ebd0980
Revises: 3b62f0dd370e
Create Date: 2026-11-02 17:22:30.110528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f6f0ebd0980'
down_revision: Union[str, Sequence[str], None] = '3b62f0dd370e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('destinatarios') as batch_op:
        batch_op.add_column(sa.Column('cliente_id', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_foreign_key(
            'fk_destinatarios_cliente_id_clientes', 'clientes', ['cliente_id'], ['id']
        )

    with op.batch_alter_table('destinatarios') as batch_op:
        batch_op.alter_column('cliente_id', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('destinatarios') as batch_op:
        batch_op.drop_constraint('fk_destinatarios_cliente_id_clientes', type_='foreignkey')
        batch_op.drop_column('cliente_id')
