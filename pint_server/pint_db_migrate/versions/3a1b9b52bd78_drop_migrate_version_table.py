"""drop migrate version table

Revision ID: 3a1b9b52bd78
Revises: 
Create Date: 2021-07-29 23:41:32.254268

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '3a1b9b52bd78'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # drop the migrate_version table from sqlalchemy-migrate
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if 'migrate_version' in tables:
        op.drop_table('migrate_version')


def downgrade():
    # there's no turning back as we no longer support sqlalchemy-migrate
    pass
